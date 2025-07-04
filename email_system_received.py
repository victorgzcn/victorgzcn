import smtplib
import sqlite3
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import json
import shutil
from datetime import datetime
import logging
from pathlib import Path

LOG_DIR = Path("email_logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "email_system.log"),
        logging.StreamHandler()
    ]
)

def log_email(recipient_email, status, details=""):
    try:
        logging.info(f"Sent to {recipient_email} | Status: {status} | {details}")
        # Also record in analytics
        EmailAnalytics.record_send(recipient_email.split('@')[0])  # Using email prefix as ID
    except Exception as e:
        logging.error(f"Failed to log email: {str(e)}")

def view_email_logs():
    """Display recent email logs"""
    log_file = LOG_DIR / "email_system.log"
    if not log_file.exists():
        print("No logs available yet")
        return
    
    print("\nRecent Email Logs:")
    print("="*50)
    with open(log_file) as f:
        for line in f.readlines()[-10:]:  # Show last 10 entries
            print(line.strip())
    print("="*50)        


# Database Configuration
DATABASE = "email_recipients.db"

# Initialize Database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            company TEXT,
            last_purchase_date TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

class EmailAnalytics:
    @staticmethod
    def record_send(recipient_id, campaign_id="default"):
        try:
            stats_file = Path("analytics/email_stats.json")
            stats_file.parent.mkdir(exist_ok=True)
            
            data = {}
            if stats_file.exists():
                with open(stats_file) as f:
                    data = json.load(f)
            
            campaign_key = f"campaign_{campaign_id}"
            
            if campaign_key not in data:
                data[campaign_key] = {
                    "total_sent": 0,
                    "last_sent": datetime.now().isoformat(),
                    "recipients": []
                }
            
            data[campaign_key]["total_sent"] += 1
            data[campaign_key]["last_sent"] = datetime.now().isoformat()
            
            # Avoid duplicate entries
            if not any(r['id'] == recipient_id for r in data[campaign_key]["recipients"]):
                data[campaign_key]["recipients"].append({
                    "id": recipient_id,
                    "sent_at": datetime.now().isoformat()
                })
            
            with open(stats_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logging.error(f"Failed to record analytics: {str(e)}")    

class EmailTemplates:
    TEMPLATES_FILE = "templates.json"
    
    TEMPLATES = {
        "welcome": {
            "subject": "Welcome to PlyFlame, {name}! Your Journey Starts Here",
            "text": """Dear {name},

    Thank you for joining PlyFlame Technologies! We're excited to have you on board.

    Here's what you can expect:
    - 24/7 customer support
    - Exclusive member discounts
    - Early access to new products

    Start exploring: https://www.plyflame.com

    Cheers,
    The PlyFlame Team""",

            "html": """<!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; }
            .header { color: #256F9C; }
            .button { background: #256F9C; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1 class="header">Welcome to PlyFlame, {name}!</h1>
        <p>Thank you for joining PlyFlame Technologies! We're excited to have you on board.</p>
    
        <h3>Here's what you can expect:</h3>
        <ul>
            <li>24/7 customer support</li>
            <li>Exclusive member discounts</li>
            <li>Early access to new products</li>
        </ul>
    
        <a href="https://www.plyflame.com" class="button">Start Exploring</a>
    
        <p>Cheers,<br>The PlyFlame Team</p>
    </body>
    </html>"""
        },
        "followup": {
            "subject": "{name}, your purchase on {last_purchase_date} - What's next?",
            "text": """Hi {name},

    We noticed your recent purchase on {last_purchase_date} and wanted to share some recommendations:

    Recommended for you:
    1. Product X (complements your purchase)
    2. Accessory Y 
    3. Maintenance Kit Z

    Enjoy 15% OFF your next order with code: FOLLOWUP15

    The PlyFlame Team""",

            "html": """<!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 600px; margin: 0 auto; }
            .product { border: 1px solid #eee; padding: 15px; margin: 10px 0; }
            .discount { background: #FFF8E1; padding: 15px; text-align: center; }
        </style>
    </head>
    <body>
        <h2>Hi {name},</h2>
        <p>We noticed your recent purchase on <strong>{last_purchase_date}</strong> and wanted to share some recommendations:</p>
    
        <h3>Recommended for you:</h3>
        <div class="product">
            <h4>Product X</h4>
            <p>Perfectly complements your purchase</p>
            <a href="https://www.plyflame.com/product-x">View Product</a>
        </div>
    
        <div class="discount">
            <h3>Enjoy 15% OFF your next order!</h3>
            <p>Use code: <strong>FOLLOWUP15</strong></p>
        </div>
    
        <p>Best regards,<br>The PlyFlame Team</p>
    </body>
    </html>"""
        }
    }

    @classmethod
    def _init_template_file(cls):
        """Initialize template file if it doesn't exist"""
        if not Path(cls.TEMPLATES_FILE).exists():
            with open(cls.TEMPLATES_FILE, 'w') as f:
                json.dump(cls.DEFAULT_TEMPLATES, f, indent=2)

    def _ensure_templates_file(cls):
        """Create templates file if it doesn't exist"""
        if not Path(cls.TEMPLATES_FILE).exists():
            with open(cls.TEMPLATES_FILE, 'w') as f:
                json.dump({}, f)

    @classmethod
    def load_templates(cls):
        """Load all templates from file"""
        cls._init_template_file()
        with open(cls.TEMPLATES_FILE) as f:
            return json.load(f)

    @classmethod
    def save_templates(cls, templates):
        """Save all templates to file"""
        with open(cls.TEMPLATES_FILE, 'w') as f:
            json.dump(templates, f, indent=2)

    @classmethod
    def get_template(cls, name):
        """Get a specific template by name"""
        templates = cls.load_templates()
        return templates.get(name)

    @classmethod
    def add_template(cls, name, template_data):
        """Add a new template to storage"""
        templates = cls.load_templates()
        templates[name] = template_data
        cls.save_templates(templates)
        return True

class RecipientDB:
    @staticmethod
    def get_all_recipients(active_only=False):
        """Get all recipients with optional active filter"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        query = "SELECT id, name, email, company, last_purchase_date, is_active FROM recipients"
        if active_only:
            query += " WHERE is_active = 1"
            
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        recipients = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return recipients

    @staticmethod
    def add_recipient(name, email, company=None, last_purchase=None):
        """Create new recipient"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO recipients (name, email, company, last_purchase_date)
                VALUES (?, ?, ?, ?)
            """, (name, email, company, last_purchase))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            print(f"✗ Email {email} already exists")
            return False
        finally:
            conn.close()

    @staticmethod
    def update_recipient(recipient_id, **fields):
        """Update recipient fields with email uniqueness check"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
    
        # Check if email is being updated and if it already exists
        if 'email' in fields:
            cursor.execute("SELECT id FROM recipients WHERE email = ? AND id != ?", 
                        (fields['email'], recipient_id))
            if cursor.fetchone():
                conn.close()
                print(f"✗ Email {fields['email']} already exists for another recipient")
                return False
    
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values())
        values.append(recipient_id)
    
        cursor.execute(f"""
            UPDATE recipients 
            SET {set_clause}
            WHERE id = ?
        """, values)
        conn.commit()
        conn.close()
        return cursor.rowcount > 0

    @staticmethod
    def delete_recipient(recipient_id):
        """Soft delete recipient"""
        return RecipientDB.update_recipient(recipient_id, is_active=0)

    @staticmethod
    def restore_recipient(recipient_id):
        """Restore soft-deleted recipient"""
        return RecipientDB.update_recipient(recipient_id, is_active=1)        

    @staticmethod
    def get_active_recipients():
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, email, company, last_purchase_date 
            FROM recipients 
            WHERE is_active = 1
        """)
        recipients = []
        for row in cursor.fetchall():
            recipients.append({
                "name": row[0],
                "email": row[1],
                "company": row[2],
                "last_purchase": "recently" if datetime.strptime(row[3], "%Y-%m-%d") > datetime.now()-timedelta(days=30) else "earlier"
            })
        conn.close()
        return recipients
    
    @staticmethod
    def get_recipient_by_id(recipient_id):
        """Retrieve recipient by ID"""
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recipients WHERE id = ?", (recipient_id,))
            return cursor.fetchone()

# Email Functions
def create_personalized_email(recipient_data):
    """Generate complete email content with all required definitions"""
    customer_name = recipient_data['name']
    last_purchase_date = recipient_data['last_purchase_date']

    if last_purchase_date:
        try:
            purchase_date = datetime.strptime(last_purchase_date, "%Y-%m-%d")
            formatted_date = purchase_date.strftime("%B %d, %Y")  # e.g., "January 15, 2023"
            is_recent = purchase_date > datetime.now() - timedelta(days=30)
        except ValueError:
            formatted_date = last_purchase_date  # Fallback to raw string if parsing fails
            is_recent = False
    else:
        formatted_date = "unknown date"
        is_recent = False  
    
    # 2. DEFAULT PRODUCT SHOWCASE (works without any product mapping)
    product_showcase = {
        "image_url": "https://manage16093941722118.yz168.cc/comdata/72944/product/20210221092522E120012622E9FBDC_s.jpg ",
        "link": "https://www.plyflame.com/Content/834530.html",
        "alt_text": "Our Newest Products",
        "description": "Check out our latest offerings"
    }

    # 3. PERSONALIZED CONTENT
    email_paragraphs = [
        f"Hi {customer_name},",
        f"We noticed you recently purchased: {formatted_date}",
        "Here's what's new for you:",
        "1. Exclusive member discounts",
        "2. New products that complement your purchase",
        "We appreciate your business!"
    ]

    # 4. DISCOUNT BANNER (smart detection)
    discount_banner = ""
    if not is_recent:  # Use the is_recent flag we calculated earlier
        discount_banner = f"""
        <div style="border: 2px dashed #FFD700; padding: 15px; margin: 20px 0; text-align: center;">
            <h3 style="color: #C00; margin-top: 0;">Exclusive 20% OFF for {customer_name.split()[0]}!</h3>
            <p style="margin-bottom: 0;">Use code: <strong>THANKYOU20</strong></p>
        </div>
        """

    # 5. PRODUCT SHOWCASE SECTION
    product_section = f"""
    <div style="text-align: center; margin: 25px 0;">
        <a href="{product_showcase['link']}?utm_source=email&utm_campaign=followup" 
           target="_blank"
           style="text-decoration: none;">
            <img src="{product_showcase['image_url']}" 
                 alt="{product_showcase['alt_text']}" 
                 style="max-width: 100%; height: auto; border: 1px solid #eee; border-radius: 4px;">
            <p style="font-size: 0.9em; color: #256F9C; margin-top: 8px;">
                {product_showcase['description']} →
            </p>
        </a>
        <p style="font-size: 0.8em; color: #999; margin-top: 5px;">
            Your last purchase: {last_purchase_date}
        </p>
    </div>
    """

    # 6. COMPLETE EMAIL TEMPLATE
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your Personalized Update</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 15px; }}
            .paragraph {{ line-height: 1.6; margin-bottom: 15px; }}
            .footer {{ color: #666; font-size: 0.9em; margin-top: 30px; text-align: center; }}
        </style>
    </head>
    <body>
        <!-- Logo -->
        <div style="text-align: center; margin-bottom: 20px;">
            <a href="https://www.plyflame.com" target="_blank">
                <img src="https://manage16093941722118.yz168.cc/comdata/72944/202506/202506291442032fc58a.png" 
                     alt="PlyFlame" width="180" style="max-width: 100%;">
            </a>
        </div>
        
        {discount_banner}
        
        {' '.join(f'<p class="paragraph">{p}</p>' for p in email_paragraphs)}
        
        {product_section}
        
        <!-- CTA Button -->
        <div style="text-align: center; margin: 25px 0;">
            <a href="https://www.plyflame.com/ProductDetail/4730963.html" 
               style="background: #256F9C; color: white; text-decoration: none; 
                      padding: 12px 25px; border-radius: 4px; font-weight: bold;
                      display: inline-block;" 
               target="_blank">
                View Your Exclusive Offers
            </a>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>
                <a href="https://www.plyflame.com" style="color: #256F9C; text-decoration: none;">
                    <strong>PlyFlame Technologies</strong>
                </a>
            </p>
            <p>
                <a href="https://www.plyflame.com/contact" style="color: #666;">Contact Us</a> | 
                <a href="https://www.plyflame.com/index.php?c=front/UserRegister" style="color: #666;">Your Account</a>
            </p>
        </div>
    </body>
    </html>
    """
    
    # 7. PLAIN TEXT VERSION
    plain_text = f"""
    Hi {customer_name},

    We noticed your recent purchase: {last_purchase_date}
    
    Here's what's new for you:
    1. Exclusive member discounts
    2. New complementary products
    
    Check out our latest: {product_showcase['link']}
    
    Thank you for choosing PlyFlame!
    
    ---
    PlyFlame Technologies
    https://www.plyflame.com
    """
    
    return plain_text, html_content

def send_personalized_email(recipient_data, smtp_config):
    """Enhanced email sending with better error handling"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = smtp_config['sender']
        msg['To'] = recipient_data['email']
        msg['Subject'] = recipient_data.get('subject', f"Your Update - {recipient_data['name']}")
        
        # Create both text and HTML versions
        text_content = recipient_data.get('body') or create_personalized_email(recipient_data)[0]
        html_content = recipient_data.get('html') or create_personalized_email(recipient_data)[1]
        
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port']) as server:
            server.login(smtp_config['sender'], smtp_config['password'])
            server.send_message(msg)  # Using send_message instead of sendmail
            
        log_email(recipient_data['email'], "Delivered")
        EmailAnalytics.record_send(recipient_data['email'].split('@')[0])
        print(f"✓ Email sent to {recipient_data['email']}")
        return True
        
    except smtplib.SMTPException as e:
        error_msg = f"SMTP Error: {str(e)}"
        log_email(recipient_data['email'], "Failed", error_msg)
        print(f"✗ Failed to send to {recipient_data['email']}: {error_msg}")
        return False
    except Exception as e:
        error_msg = f"Unexpected Error: {str(e)}"
        log_email(recipient_data['email'], "Failed", error_msg)
        print(f"✗ Failed to send to {recipient_data['email']}: {error_msg}")
        return False

def send_standard_campaign(recipients, smtp_config):
    for recipient in recipients:
        send_personalized_email({
            'name': recipient['name'],
            'email': recipient['email'],
            'company': recipient['company'],
            'last_purchase_date': recipient['last_purchase_date']
        }, smtp_config)
        time.sleep(1)

def send_template_campaign(recipients, smtp_config, template_name):
    """Send campaign using a predefined template"""
    template = EmailTemplates.get_template(template_name)
    
    for recipient in recipients:
        try:
            # Format template with recipient data
            email_data = {
                'name': recipient['name'],
                'email': recipient['email'],
                'company': recipient.get('company', ''),
                'last_purchase_date': recipient.get('last_purchase_date', 'recently'),
                'subject': template['subject'].format(**recipient),
                'body': template['text'].format(**recipient),
                'html': template['html'].format(**recipient)
            }
            
            # Send the email
            if send_personalized_email(email_data, smtp_config):
                # Record in analytics
                EmailAnalytics.record_send(
                    recipient_id=recipient['email'].split('@')[0],
                    campaign_id=f"template_{template_name}"
                )
            
            time.sleep(1)  # Rate limiting
            
        except KeyError as e:
            print(f"✗ Missing data for {recipient['email']}: {str(e)}")
            continue

def send_test_batch(recipients, smtp_config):
    print("\n" + "="*50)
    print("TEST BATCH MODE (First 5 recipients)".center(50))
    print("="*50)
    for recipient in recipients:
        print(f"TEST: Would send to {recipient['email']}")
        print(f"Name: {recipient['name']}")
        print(f"Last Purchase: {recipient['last_purchase_date']}\n")

def list_templates():
    print("\nAvailable Templates:")
    for name, template in EmailTemplates.TEMPLATES.items():
        print(f"- {name}: {template['subject']}")

def get_multiline_input(prompt=None):
    """Get multiline input from user"""
    if prompt:
        print(prompt)
    print("Type your content. Press Enter twice to finish:")
    lines = []
    while True:
        line = input()
        if not line and lines and not lines[-1]:  # Two empty lines
            break
        lines.append(line)
    return '\n'.join(lines).strip()

def get_multiline_input(prompt=None):
    """Get multiline input from user"""
    if prompt:
        print(prompt)
    print("Type your content. Press Enter twice to finish:")
    lines = []
    while True:
        line = input()
        if not line and lines and not lines[-1]:  # Two empty lines
            break
        lines.append(line)
    return '\n'.join(lines).strip()

def preview_template(template_name):
    """Preview a template with sample data"""
    template = EmailTemplates.get_template(template_name)
    if not template:
        print(f"✗ Template '{template_name}' not found")
        return
    
    sample_data = {
        'name': 'Sample Customer',
        'email': 'sample@example.com',
        'company': 'Sample Inc',
        'last_purchase_date': datetime.now().strftime('%Y-%m-%d')
    }
    
    print("\n" + "="*50)
    print(f"TEMPLATE PREVIEW: {template_name}".center(50))
    print("="*50)
    print(f"\nSUBJECT:\n{template['subject'].format(**sample_data)}")
    print("\nTEXT VERSION:\n" + "-"*50)
    print(template['text'].format(**sample_data))
    print("-"*50)
    
    if input("\nShow HTML preview in browser? (y/n): ").lower() == 'y':
        try:
            import webbrowser
            from tempfile import NamedTemporaryFile
            
            html_content = template['html'].format(**sample_data)
            with NamedTemporaryFile('w', delete=False, suffix='.html') as f:
                f.write(html_content)
                webbrowser.open(f.name)
        except Exception as e:
            print(f"Couldn't open browser preview: {str(e)}")
            print("\nHTML CONTENT:\n" + "-"*50)
            print(template['html'].format(**sample_data))
            print("-"*50)
            
def get_html_input():
    print("\nEnter HTML content (type 'END' on a new line to finish):")
    print("""HTML Tips:
    - Start with: <html><body>
    - End with: </body></html>
    - Use inline styles: style="color:blue;"
    - Images: <img src="URL" width="300">
    """)
    
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == 'END':
                break
            lines.append(line)
        except EOFError:
            break
            
    html = '\n'.join(lines)
    
    # Basic validation
    if not html.strip().startswith('<html>'):
        print("⚠ Warning: HTML should start with <html> tag")
    if not html.strip().endswith('</html>'):
        print("⚠ Warning: HTML should end with </html> tag")
        
    return html
    
def send_with_template(template_name, recipients, smtp_config):
    """Send emails using a specific template"""
    template = EmailTemplates.get_template(template_name)
    if not template:
        print(f"✗ Template '{template_name}' not found")
        return

    for recipient in recipients:
        try:
            # Prepare email data
            email_data = {
                'name': recipient['name'],
                'email': recipient['email'],
                'company': recipient.get('company', ''),
                'last_purchase_date': recipient.get('last_purchase_date', 'recently'),
                'subject': template['subject'].format(**recipient),
                'body': template['text'].format(**recipient),
                'html': template['html'].format(**recipient)
            }

            # Send the email
            if send_personalized_email(email_data, smtp_config):
                print(f"✓ Sent {template_name} template to {recipient['email']}")
            else:
                print(f"✗ Failed to send to {recipient['email']}")

            time.sleep(1)  # Rate limiting

        except Exception as e:
            print(f"✗ Error sending to {recipient['email']}: {str(e)}")

def add_new_template():
    print("\n" + "="*50)
    print("ADD NEW TEMPLATE".center(50))
    print("="*50)
    
    name = input("Template name: ").strip()
    if EmailTemplates.get_template(name):
        print(f"✗ Template '{name}' already exists")
        return False
    
    print("\nEnter the email subject (use {placeholders} for variables):")
    subject = input("Subject: ").strip()
    
    print("\nEnter the plain text version (press Enter twice to finish):")
    text_lines = []
    while True:
        line = input()
        if not line and text_lines and not text_lines[-1]:
            break
        text_lines.append(line)
    text = '\n'.join(text_lines)
    
    print("\nEnter the HTML version (press Enter twice to finish):")
    print("""HTML Tips:
    - Start with: <html><body>...</body></html>
    - Use inline styles: style="color:blue;"
    - Images: <img src="URL" width="300">
    """)
    html_lines = []
    while True:
        line = input()
        if not line and html_lines and not html_lines[-1]:
            break
        html_lines.append(line)
    html = '\n'.join(html_lines)
    
    if EmailTemplates.add_template(name, {
        'subject': subject,
        'text': text,
        'html': html
    }):
        print(f"✓ Template '{name}' added successfully!")
        return True
    
    print(f"✗ Failed to add template '{name}'")
    return False                       

        
def show_analytics():
    try:
        analytics_dir = Path("analytics")
        analytics_dir.mkdir(exist_ok=True)
        stats_file = analytics_dir / "email_stats.json"
        
        if not stats_file.exists():
            print("No analytics data available yet")
            return
            
        with open(stats_file) as f:
            data = json.load(f)
            print("\nEmail Analytics:")
            print("="*50)
            for campaign, stats in data.items():
                print(f"\nCampaign: {campaign}")
                print(f"Total Sent: {stats['total_sent']}")
                print(f"Last Sent: {stats['last_sent']}")
                print(f"Unique Recipients: {len(stats['recipients'])}")
            print("="*50)
    except Exception as e:
        print(f"✗ Error loading analytics: {str(e)}")

def backup_database():
    try:
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"email_recipients_{timestamp}.db"
        shutil.copy2(DATABASE, backup_file)
        print(f"✓ Database backed up to {backup_file}")
        return True
    except Exception as e:
        print(f"✗ Backup failed: {str(e)}")
        return False 

def test_smtp_connection(smtp_config):
    """Verify SMTP credentials and connection"""
    try:
        with smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port']) as server:
            server.login(smtp_config['sender'], smtp_config['password'])
            print("✓ SMTP Connection Successful")
            return True
    except Exception as e:
        print(f"✗ SMTP Connection Failed: {str(e)}")
        return False 

def send_test_batch(recipients, smtp_config, template_name="default"):
    """Send test emails to first 5 recipients with optional template"""
    print("\n" + "="*50)
    print("TEST BATCH MODE (First 5 recipients)".center(50))
    print("="*50)
    
    test_recipients = recipients[:5]
    
    # Get template if specified
    template = EmailTemplates.get_template(template_name) if template_name else None
    
    for recipient in test_recipients:
        email_data = {
            'name': recipient['name'],
            'email': recipient['email'],
            'company': recipient['company'],
            'last_purchase_date': recipient['last_purchase_date'],
            'test_mode': True
        }
        
        # Apply template if available
        if template:
            email_data.update({
                'subject': template['subject'].format(**recipient),
                'body': template['text'].format(**recipient)
            })
        
        try:
            # Modified send function that respects test mode
            if email_data.get('test_mode'):
                print(f"TEST: Would send to {email_data['email']}")
                print(f"Subject: {email_data.get('subject', 'Default Subject')}")
                print(f"Content: {email_data.get('body', 'Default content')[:100]}...\n")
            else:
                send_personalized_email(email_data, smtp_config)
            
            time.sleep(1)
        except Exception as e:
            print(f"✗ Failed test send to {recipient['email']}: {str(e)}")


def show_template_preview(template_name):
    template = EmailTemplates.get_template(template_name)
    print("\nTemplate Preview:")
    print(f"Subject: {template['subject']}")
    print(f"Content: {template['text'][:100]}...")

def preview_template(template_name):
    """Preview a template with sample data"""
    template = EmailTemplates.get_template(template_name)
    if not template:
        print(f"✗ Template '{template_name}' not found")
        return

    sample_data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'company': 'ACME Corp',
        'last_purchase_date': '2023-01-15'
    }

    print("\n" + "="*50)
    print(f"PREVIEW: {template_name}".center(50))
    print("="*50)
    print(f"\nSUBJECT:\n{template['subject'].format(**sample_data)}")
    print("\nTEXT VERSION:\n" + "-"*50)
    print(template['text'].format(**sample_data))
    print("-"*50)
    
    if input("\nShow HTML preview? (y/n): ").lower() == 'y':
        try:
            import webbrowser
            from tempfile import NamedTemporaryFile
            
            html_content = template['html'].format(**sample_data)
            with NamedTemporaryFile('w', delete=False, suffix='.html') as f:
                f.write(html_content)
                webbrowser.open(f.name)
        except Exception as e:
            print(f"Couldn't open browser preview: {str(e)}")
            print("\nHTML CONTENT:\n" + "-"*50)
            print(template['html'].format(**sample_data))
            print("-"*50)

def preview_template_menu():
    """Show template preview interface"""
    templates = EmailTemplates.load_templates()
    if not templates:
        print("No templates available!")
        return
    
    print("\nAvailable Templates:")
    for name in templates:
        print(f"- {name}")
    
    template_name = input("\nEnter template name to preview: ")
    if template_name not in templates:
        print(f"✗ Template '{template_name}' not found")
        return
    
    preview_template(template_name)

def add_new_template():
    """Handle new template creation"""
    print("\n" + "="*50)
    print("ADD NEW TEMPLATE".center(50))
    print("="*50)
    
    name = input("Template name: ").strip()
    if EmailTemplates.get_template(name):
        print(f"✗ Template '{name}' already exists")
        return False
    
    subject = input("Email subject (use {placeholders}): ").strip()
    
    print("\nEnter plain text version (press Enter twice to finish):")
    text = get_multiline_input()
    
    print("\nEnter HTML version (press Enter twice to finish):")
    print("HTML Tips: Use <html><body>...</body></html> structure")
    html = get_multiline_input()
    
    if EmailTemplates.add_template(name, {
        'subject': subject,
        'text': text,
        'html': html
    }):
        print(f"✓ Template '{name}' added successfully!")
        return True
    
    print(f"✗ Failed to add template '{name}'")
    return False

def edit_existing_template():
    """Edit an existing template"""
    templates = EmailTemplates.load_templates()
    if not templates:
        print("No templates available to edit!")
        return
    
    print("\nAvailable Templates:")
    for name in templates:
        print(f"- {name}")
    
    template_name = input("\nEnter template name to edit: ")
    if template_name not in templates:
        print(f"✗ Template '{template_name}' not found")
        return
    
    template = templates[template_name]
    print(f"\nEditing template: {template_name}")
    
    # Edit subject
    print(f"\nCurrent subject: {template['subject']}")
    new_subject = input("New subject (leave blank to keep current): ").strip()
    if new_subject:
        template['subject'] = new_subject
    
    # Edit text content
    print("\nCurrent text content:")
    print("-"*50)
    print(template['text'])
    print("-"*50)
    if input("Edit text content? (y/n): ").lower() == 'y':
        print("Enter new text content:")
        template['text'] = get_multiline_input()
    
    # Edit HTML content
    print("\nCurrent HTML content:")
    print("-"*50)
    print(template['html'])
    print("-"*50)
    if input("Edit HTML content? (y/n): ").lower() == 'y':
        print("Enter new HTML content:")
        template['html'] = get_multiline_input()
    
    if EmailTemplates.add_template(template_name, template):
        print(f"✓ Template '{template_name}' updated successfully!")
    else:
        print(f"✗ Failed to update template '{template_name}'")

def send_using_template(template_name, recipients, smtp_config):
    """Send emails to recipients using a selected template"""
    # Get active recipients
    recipients = RecipientDB.get_active_recipients()
    if not recipients:
        print("No active recipients available!")
        return False

    # Load available templates
    templates = EmailTemplates.load_templates()
    if not templates:
        print("No templates available!")
        return False

    # Show template selection
    print("\nAvailable Templates:")
    for name in templates:
        print(f"- {name}")

    # Select template
    template_name = input("\nEnter template name to use: ")
    if template_name not in templates:
        print(f"Error: Template '{template_name}' not found")
        return False

    # Verify SMTP configuration
    if not smtp_config.get('password'):
        smtp_config['password'] = input("Enter SMTP password: ")

    # Confirm before sending
    confirm = input(f"\nSend to {len(recipients)} recipients? (y/n): ")
    if confirm.lower() != 'y':
        print("Sending cancelled.")
        return False

    # Send emails
    success_count = 0
    for recipient in recipients:
        try:
            # Prepare email data with template and recipient info
            email_data = {
                'name': recipient['name'],
                'email': recipient['email'],
                'company': recipient.get('company', ''),
                'last_purchase_date': recipient.get('last_purchase_date', 'recently'),
                'subject': templates[template_name]['subject'].format(**recipient),
                'body': templates[template_name]['text'].format(**recipient),
                'html': templates[template_name]['html'].format(**recipient)
            }

            # Send the email
            if send_personalized_email(email_data, smtp_config):
                success_count += 1
                # Record in analytics
                EmailAnalytics.record_send(recipient['email'], f"template_{template_name}")
            time.sleep(1)  # Rate limiting

        except Exception as e:
            print(f"✗ Failed to send to {recipient['email']}: {str(e)}")

    # Show results
    print(f"\nCampaign completed. Successfully sent to {success_count}/{len(recipients)} recipients")
    return success_count > 0

def validate_template(template):
    required = ['subject', 'text', 'html']
    return all(key in template for key in required)

def check_content_parity(text, html):
    # Ensure all key info exists in both versions
    key_info = ['offer', 'deadline', 'contact']
    return all(info in text.lower() and info in html.lower() for info in key_info)


# Menu Interface
def show_menu():
    print("\n" + "="*50)
    print("EMAIL MARKETING SYSTEM".center(50))
    print("="*50)
    print("1. Manage Recipients")
    print("2. Send Emails")
    print("3. Configure SMTP")
    print("4. Backup Database")
    print("5. Email Templates")  # New template system
    print("6. View Analytics")
    print("7. Exit")
    
    while True:
        choice = input("Enter your choice (1-7): ")
        if choice in ['1', '2', '3', '4', '5', '6', '7']:
            return choice
        print("Invalid choice. Please try again.")

def manage_recipients_menu():
    while True:
        print("\n" + "="*50)
        print("RECIPIENT MANAGEMENT".center(50))
        print("="*50)
        print("1. Add New Recipient")
        print("2. View All Recipients")
        print("3. Update Recipient")
        print("4. Delete/Restore Recipient")
        print("5. Toggle active status")
        print("6. Back to Main Menu")
        print("="*50)
        
        choice = input("Enter your choice (1-6): ")
        
        if choice == "1":
            print("\nAdd New Recipient")
            name = input("Full Name: ").strip()
            email = input("Email: ").strip()
            company = input("Company (optional): ").strip()
            last_purchase = input("Last Purchase Date (YYYY-MM-DD): ").strip()
            if RecipientDB.add_recipient(name, email, company or None, last_purchase or None):
                print("✓ Recipient added successfully!")
        
        elif choice == "2":
            recipients = RecipientDB.get_all_recipients()
            print("\nAll Recipients:")
            print("-"*85)
            print(f"{'ID':<5}{'Name':<20}{'Email':<30}{'Company':<20}{'Status':<10}")
            print("-"*85)
            for r in recipients:
                status = "Active" if r['is_active'] else "Inactive"
                print(f"{r['id']:<5}{r['name']:<20}{r['email']:<30}{r['company'] or 'N/A':<20}{status:<10}")
        
        elif choice == "3":
            recipient_id = input("Enter recipient ID to edit: ")
            recipients = RecipientDB.get_all_recipients()
            recipient = next((r for r in recipients if str(r['id']) == recipient_id), None)
    
            if recipient:
                print(f"\nEditing: {recipient['name']} <{recipient['email']}>")
                updates = {}
                if name := input(f"New name [{recipient['name']}]: ").strip():
                    updates['name'] = name
                if email := input(f"New email [{recipient['email']}]: ").strip():
                        updates['email'] = email
                if company := input(f"New company [{recipient['company'] or 'N/A'}]: ").strip():
                    updates['company'] = company if company != 'N/A' else None
                if last_purchase := input(f"New last purchase date [{recipient['last_purchase_date'] or 'N/A'}]: ").strip():
                    updates['last_purchase_date'] = last_purchase if last_purchase != 'N/A' else None
        
                if updates:
                    if not RecipientDB.update_recipient(recipient['id'], **updates):
                        print("✗ Update failed (possibly due to duplicate email)")
                    else:
                        print("✓ Recipient updated!")
                else:
                    print("No changes made.")
            else:
                print("✗ Recipient not found")
        
        elif choice == "4":
            recipient_id = input("Enter recipient ID to toggle status: ")
            recipients = RecipientDB.get_all_recipients()
            recipient = next((r for r in recipients if str(r['id']) == recipient_id), None)
            
            if recipient:
                action = "restore" if not recipient['is_active'] else "delete"
                if input(f"Confirm {action} {recipient['email']}? (y/n): ").lower() == 'y':
                    if action == "delete":
                        success = RecipientDB.delete_recipient(recipient['id'])
                    else:
                        success = RecipientDB.restore_recipient(recipient['id'])
                    
                    if success:
                        print(f"✓ Recipient {action}d successfully!")
                    else:
                        print("✗ Operation failed")
            else:
                print("✗ Recipient not found")
                
        elif choice == "5":
            recipient_id = input("Enter recipient ID to toggle active status: ")
    
            # First get the current recipient data
            recipient = RecipientDB.get_recipient_by_id(recipient_id)
    
            if not recipient:
                print("Error: Recipient not found")
                continue
    
            current_status = bool(recipient['is_active'])
            new_status = not current_status
    
            # Confirm with user
            print(f"\nCurrent status: {'Active' if current_status else 'Inactive'}")
            confirm = input(f"Change status to {'Inactive' if current_status else 'Active'}? (y/n): ")
    
            if confirm.lower() == 'y':
                if RecipientDB.update_recipient(recipient_id, is_active=new_status):
                    print(f"Status updated to {'Active' if new_status else 'Inactive'}")
                else:
                    print("Failed to update status")
            else:
                print("Status change cancelled")

        elif choice == "6":
            break
            
        else:
            print("Invalid choice. Please try again.")

def send_emails_menu(smtp_config):
    while True:
        recipients = RecipientDB.get_all_recipients(active_only=True)
        if not recipients:
            print("No active recipients found!")
            return
            
        print("\n" + "="*50)
        print("SEND EMAILS".center(50))
        print("="*50)
        print("1. Send to ALL active recipients")
        print("2. Select specific recipients")
        print("3. Standard Campaign")
        print("4. Template Campaign")
        print("5. Test Batch (5 recipients)")
        print("6. Back to Main Menu")
        print("="*50)
        
        choice = input("Enter your choice (1-6): ")
        
        if choice == "1":
            if input(f"Send to ALL {len(recipients)} active recipients? (y/n): ").lower() != 'y':
                continue
                
            if not smtp_config['password']:
                smtp_config['password'] = input("Enter SMTP password: ")
            
            for recipient in recipients:
                send_personalized_email({
                    'name': recipient['name'],
                    'email': recipient['email'],
                    'company': recipient['company'],
                    'last_purchase_date': recipient['last_purchase_date']
                }, smtp_config)
                time.sleep(1)  # Rate limiting
        
        elif choice == "2":
            print("\nSelect recipients (comma-separated IDs):")
            for r in recipients:
                print(f"{r['id']}: {r['name']} <{r['email']}>")
            
            selected_ids = input("Enter IDs: ").split(',')
            selected_recipients = [r for r in recipients if str(r['id']) in [id.strip() for id in selected_ids]]
            
            if not selected_recipients:
                print("No valid recipients selected!")
                continue
                
            if not smtp_config['password']:
                smtp_config['password'] = input("Enter SMTP password: ")
            
            for recipient in selected_recipients:
                send_personalized_email({
                    'name': recipient['name'],
                    'email': recipient['email'],
                    'company': recipient['company'],
                    'last_purchase_date': recipient['last_purchase_date']  
                }, smtp_config)
                time.sleep(1)

        elif choice == "3":
            send_standard_campaign(recipients, smtp_config)
            
        elif choice == "4":  # Template Campaign
            template_name = input("Enter template name: ")
            if not smtp_config.get('password'):
                smtp_config['password'] = input("Enter SMTP password: ")
            send_template_campaign(recipients,template_name, smtp_config)
            
        elif choice == "5":
            send_test_batch(recipients[:5], smtp_config)      
           
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please try again.")

def manage_templates(smtp_config=None):
    # Initialize default SMTP config if not provided
    if smtp_config is None:
        smtp_config = {
            'server': 'smtp.qiye.aliyun.com',
            'port': 465,
            'sender': 'victor@plyflame.com',
            'password': None
        }

    while True:
        print("\n" + "="*50)
        print("TEMPLATE MANAGEMENT".center(50))
        print("="*50)
        print("1. List All Templates")
        print("2. Preview Template")
        print("3. Add New Template (saves to templates.json)")
        print("4. Edit Existing Template")
        print("5. Send Using Template")
        print("6. Back to Main Menu")
        print("="*50)
        
        choice = input("Enter your choice (1-6): ")
        
        if choice == "1":
            print("\nAvailable Templates:")
            print("-"*50)
            templates = EmailTemplates.load_templates()
            for name, template in templates.items():
                print(f"{name}: {template['subject']}")
            print("-"*50)
        
        elif choice == "2":
            templates = EmailTemplates.load_templates()
            if not templates:
                print("No templates available!")
                continue
                
            print("\nAvailable Templates:")
            for name in templates:
                print(f"- {name}")
                
            template_name = input("Enter template name to preview: ")
            if template_name not in templates:
                print(f"Template '{template_name}' not found")
                continue
                
            preview_template(template_name)
            
        elif choice == "3":
            print("\n" + "="*50)
            print("ADD NEW TEMPLATE".center(50))
            print("="*50)
            
            name = input("Template name: ").strip()
            if EmailTemplates.get_template(name):
                print(f"Template '{name}' already exists")
                continue
                
            print("\nTemplate variables available: {name}, {email}, {company}, {last_purchase_date}")
            
            print("\nEnter email subject (use variables where needed):")
            subject = input("Subject: ").strip()
            
            print("\nEnter plain text version:")
            print("Example:\nHi {name},\n\nThank you for your purchase on {last_purchase_date}...")
            text = get_multiline_input()
            
            print("\nEnter HTML version:")
            print("""HTML Example:
<html>
<body>
    <h1>Hello {name}!</h1>
    <p>Thank you for your purchase on {last_purchase_date}</p>
    <a href="https://example.com">Visit us</a>
</body>
</html>""")
            html = get_multiline_input()
            
            if EmailTemplates.add_template(name, {
                'subject': subject,
                'text': text,
                'html': html
            }):
                print(f"\n✓ Template '{name}' saved to templates.json")
            else:
                print("\n✗ Failed to save template")
                
        elif choice == "4":
            templates = EmailTemplates.load_templates()
            if not templates:
                print("No templates available to edit!")
                continue
                
            print("\nAvailable Templates:")
            for name in templates:
                print(f"- {name}")
                
            template_name = input("\nEnter template name to edit: ")
            if template_name not in templates:
                print(f"Template '{template_name}' not found")
                continue
                
            template = templates[template_name]
            print(f"\nEditing template: {template_name}")
            
            # Edit subject
            print(f"\nCurrent subject: {template['subject']}")
            new_subject = input("New subject (leave blank to keep current): ").strip()
            if new_subject:
                template['subject'] = new_subject
                
            # Edit text content
            print("\nCurrent text content:")
            print("-"*50)
            print(template['text'])
            print("-"*50)
            if input("Edit text content? (y/n): ").lower() == 'y':
                print("Enter new text content:")
                template['text'] = get_multiline_input()
                
            # Edit HTML content
            print("\nCurrent HTML content:")
            print("-"*50)
            print(template['html'])
            print("-"*50)
            if input("Edit HTML content? (y/n): ").lower() == 'y':
                print("Enter new HTML content:")
                template['html'] = get_multiline_input()
                
            if EmailTemplates.add_template(template_name, template):
                print(f"\n✓ Template '{template_name}' updated in templates.json")
            else:
                print("\n✗ Failed to update template")
                
        elif choice == "5":
            # Get all active recipients first
            all_recipients = RecipientDB.get_active_recipients()
            if not all_recipients:
                print("No active recipients available!")
                continue
                
            # Template selection
            templates = EmailTemplates.load_templates()
            print("\nAvailable Templates:")
            for name in templates:
                print(f"- {name}")
                
            template_name = input("\nEnter template name to use: ")
            if template_name not in templates:
                print(f"Template '{template_name}' not found")
                continue
                
            # Recipient selection
            print("\nRecipient Options:")
            print("1. Send to all active recipients")
            print("2. Select specific recipients")
            recipient_choice = input("Choose recipient option (1-2): ")
            
            if recipient_choice == "1":
                recipients = all_recipients
            elif recipient_choice == "2":
                print("\nAvailable Recipients:")
                for i, recipient in enumerate(all_recipients, 1):
                    print(f"{i}. {recipient['name']} <{recipient['email']}>")
                    
                selected = input("\nEnter recipient numbers (comma separated): ").split(',')
                try:
                    selected_indices = [int(s.strip())-1 for s in selected]
                    recipients = [all_recipients[i] for i in selected_indices 
                                 if 0 <= i < len(all_recipients)]
                except (ValueError, IndexError):
                    print("Invalid selection")
                    continue
            else:
                print("Invalid choice")
                continue
                
            if not recipients:
                print("No recipients selected")
                continue
                
            # SMTP password
            if not smtp_config.get('password'):
                smtp_config['password'] = input("Enter SMTP password: ")
                
            # Confirmation
            print(f"\nAbout to send to {len(recipients)} recipients:")
            for recipient in recipients:
                print(f"- {recipient['name']} <{recipient['email']}>")
                
            if input("\nConfirm sending? (y/n): ").lower() != 'y':
                print("Sending cancelled")
                continue
                
            # Send emails
            print("\nSending emails...")
            success_count = 0
            for recipient in recipients:
                try:
                    email_data = {
                        'name': recipient['name'],
                        'email': recipient['email'],
                        'company': recipient.get('company', ''),
                        'last_purchase_date': recipient.get('last_purchase_date', 'recently'),
                        'subject': templates[template_name]['subject'].format(**recipient),
                        'body': templates[template_name]['text'].format(**recipient),
                        'html': templates[template_name]['html'].format(**recipient)
                    }
                    
                    if send_personalized_email(email_data, smtp_config):
                        success_count += 1
                        EmailAnalytics.record_send(recipient['email'].split('@')[0], 
                                                  f"template_{template_name}")
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"✗ Failed to send to {recipient['email']}: {str(e)}")
                    
            print("\n" + "="*50)
            print(f"✓ Campaign completed!".center(50))
            print(f"Successfully sent to {success_count}/{len(recipients)} recipients".center(50))
            print("="*50)
            
        elif choice == "6":
            break
            
        else:
            print("Invalid choice, please try again")


def main():
    init_db()
    smtp_config = {
        'server': 'smtp.qiye.aliyun.com',
        'port': 465,
        'sender': 'victor@plyflame.com',
        'password': None
    }

    Path("backups").mkdir(exist_ok=True)
    Path("analytics").mkdir(exist_ok=True)
    Path("email_logs").mkdir(exist_ok=True)
    
    # Load templates
    EmailTemplates.load_templates()
    
    while True:
        choice = show_menu()
        
        if choice == "1":
            manage_recipients_menu()
        elif choice == "2":
            send_emails_menu(smtp_config)
        elif choice == "3":
            print("\nSMTP Configuration")
            smtp_config['server'] = input(f"SMTP Server [{smtp_config['server']}]: ") or smtp_config['server']
            smtp_config['port'] = int(input(f"SMTP Port [{smtp_config['port']}]: ") or smtp_config['port'])
            smtp_config['sender'] = input(f"Sender Email [{smtp_config['sender']}]: ") or smtp_config['sender']
        elif choice == "4":
            backup_database()
        elif choice == "5":
            manage_templates()
        elif choice == "6":
            show_analytics()
        elif choice == "7":
            print("Goodbye!")
            break

if __name__ == "__main__":
    main()