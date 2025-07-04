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
    """Send email with SMTP"""
    plain_text, html_content = create_personalized_email(recipient_data)
        
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = smtp_config['sender']
        msg['To'] = recipient_data['email']
        msg['Subject'] = f"Your Personalized Update - {recipient_data['name']}"
        
        msg.attach(MIMEText(plain_text, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port']) as server:
            server.login(smtp_config['sender'], smtp_config['password'])
            server.sendmail(smtp_config['sender'], [recipient_data['email']], msg.as_string())
        
        print(f"✓ Email sent to {recipient_data['email']}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to send to {recipient_data['email']}: {str(e)}")
        return False
    
class EmailTemplates:
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
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 15px; }}
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

    TEMPLATES["anniversary"] = {
        "subject": "Happy Anniversary, {name}! Special Gift Inside",
        "text": """Dear {name},
    
    Congratulations on your 1-year anniversary with PlyFlame!
    As a thank you, here's a 20% discount code: ANNIV20
    
    The PlyFlame Team""",
        "html": """..."""
    }

    @classmethod
    def get_template(cls, name):
        return cls.TEMPLATES.get(name, {
            "subject": "Your update",
            "text": "Hello {name}",
            "html": "<html>Default template</html>"
        })        
    template_name, recipients, smtp_config

def manage_templates():
    while True:
        print("\n" + "="*50)
        print("TEMPLATE MANAGEMENT".center(50))
        print("="*50)
        print("1. List All Templates")
        print("2. Preview Template")
        print("3. Add New Template")
        print("4. Edit Existing Template")
        print("5. Send Using Template")
        print("6. Back to Main Menu")
        print("="*50)
        
        choice = input("Enter your choice (1-6): ")
        
        if choice == "1":
            print("\nAvailable Templates:")
            print("-"*50)
            for name in EmailTemplates.TEMPLATES.keys():
                print(f"- {name}")
            print("-"*50)
        
        elif choice == "2":
            template_name = input("Enter template name to preview: ")
            if template_name in EmailTemplates.TEMPLATES:
                preview_template(template_name)
            else:
                print(f"✗ Template '{template_name}' not found")
                
        elif choice == "3":
            print("\nAdd New Template")
            name = input("Template name: ").strip()
            if name in EmailTemplates.TEMPLATES:
                print(f"✗ Template '{name}' already exists")
                continue
                
            subject = input("Email subject (use {placeholders}): ").strip()
            print("\nEnter text content (press Enter twice to finish):")
            text_lines = []
            while True:
                line = input()
                if not line and text_lines and not text_lines[-1]:
                    break
                text_lines.append(line)
            text = '\n'.join(text_lines).strip()
            
            print("\nEnter HTML content (press Enter twice to finish):")
            html_lines = []
            while True:
                line = input()
                if not line and html_lines and not html_lines[-1]:
                    break
                html_lines.append(line)
            html = '\n'.join(html_lines).strip()
            
            EmailTemplates.TEMPLATES[name] = {
                'subject': subject,
                'text': text,
                'html': html
            }
            print(f"✓ Template '{name}' added successfully!")
            
        elif choice == "4":
            template_name = input("Enter template name to edit: ")
            if template_name not in EmailTemplates.TEMPLATES:
                print(f"✗ Template '{template_name}' not found")
                continue
                
            template = EmailTemplates.TEMPLATES[template_name]
            print(f"\nEditing template: {template_name}")
            print(f"Current subject: {template['subject']}")
            new_subject = input("New subject (leave blank to keep current): ").strip()
            if new_subject:
                template['subject'] = new_subject
                
            print("\nCurrent text content:")
            print("-"*50)
            print(template['text'])
            print("-"*50)
            if input("Edit text content? (y/n): ").lower() == 'y':
                print("Enter new text content (press Enter twice to finish):")
                text_lines = []
                while True:
                    line = input()
                    if not line and text_lines and not text_lines[-1]:
                        break
                    text_lines.append(line)
                template['text'] = '\n'.join(text_lines).strip()
                
            print("\nCurrent HTML content:")
            print("-"*50)
            print(template['html'])
            print("-"*50)
            if input("Edit HTML content? (y/n): ").lower() == 'y':
                print("Enter new HTML content (press Enter twice to finish):")
                html_lines = []
                while True:
                    line = input()
                    if not line and html_lines and not html_lines[-1]:
                        break
                    html_lines.append(line)
                template['html'] = '\n'.join(html_lines).strip()
                
            print(f"✓ Template '{template_name}' updated successfully!")

        elif choice == "5":
            recipients = RecipientDB.get_active_recipients()
            if not recipients:
                print("No active recipients found!")
                continue
                
            template_name = input("Template name to use: ")
            if not EmailTemplates.get_template(template_name):
                print(f"Template '{template_name}' not found")
                continue
                
            if input(f"Send to {len(recipients)} recipients? (y/n): ").lower() == 'y':
                send_with_template()    
            
        elif choice == "6":
            break
            
        else:
            print("Invalid choice. Please try again.")

def reply_to_email(original_email, smtp_config=None):
    """Create a reply to the selected email"""
    print("\n" + "="*50)
    print("COMPOSE REPLY".center(50))
    print("="*50)
    
    # Extract the original sender
    original_sender = original_email['from']
    original_subject = original_email['subject']
    
    # Prepare reply headers
    reply_subject = f"Re: {original_subject}" if not original_subject.startswith('Re:') else original_subject
    
    print(f"Replying to: {original_sender}")
    print(f"Subject: {reply_subject}")
    print("-"*50)
    
    # Include original message as quote
    quoted_body = f"\n\n----- Original Message -----\nFrom: {original_sender}\n"
    quoted_body += f"Date: {original_email['date']}\nSubject: {original_subject}\n\n"
    quoted_body += "\n".join(f"> {line}" for line in original_email['body'].split('\n'))
    
    # Get reply content
    print("Enter your reply (press Enter twice to finish):")
    reply_content = get_multiline_input()
    full_content = f"{reply_content}{quoted_body}"
    
    # Create both text and HTML versions
    text_version = full_content
    html_version = f"""<html>
<body>
    <p>{reply_content.replace('\n', '<br>')}</p>
    <blockquote style="border-left: 2px solid #256F9C; padding-left: 10px; color: #555;">
        <small>
            <strong>Original Message</strong><br>
            From: {original_sender}<br>
            Date: {original_email['date']}<br>
            Subject: {original_subject}
        </small>
        <p>{original_email['body'].replace('\n', '<br>')}</p>
    </blockquote>
</body>
</html>"""
    
    # Send the reply
    if smtp_config:
        email_data = {
            'to': original_sender,
            'subject': reply_subject,
            'body': text_version,
            'html': html_version
        }
        return send_personalized_email(email_data, smtp_config)
    else:
        print("\nReply prepared but not sent (SMTP not configured)")
        print("\nText Version:")
        print("-"*50)
        print(text_version)
        print("-"*50)
        return False                