class EmailTemplates:
    TEMPLATES = {
        "welcome": {
            "subject": "Welcome {name}!",
            "text": "Dear {name},\n\nThank you for joining..."
        },
        "followup": {
            "subject": "About your purchase from {last_purchase_date}",
            "text": "Hello {name},\n\nWe noticed you purchased..."
        }
    }

    @classmethod
    def get_template(cls, name):
        return cls.TEMPLATES.get(name, {
            "subject": "Your update",
            "text": "Hello {name}"
        })

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