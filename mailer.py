import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

load_dotenv()

# Mailer server
smtp_server = os.getenv("MAILER_SERVER")
# Mailer port
smtp_port = os.getenv("MAILER_PORT")
# Email ID of sender
smtp_username = os.getenv("EMAIL_ID")
# Email password of sender
smtp_password = os.getenv("EMAIL_PASSWORD")
# Recipient for email
recipient = os.getenv("RECIPIENT")

def send_contact_email(data):
    # DATA from user
    email = str(data.get('email'))
    name = str(data.get('name'))
    surname = str(data.get('surname'))
    message = str(data.get('message'))
    phone = str(data.get('phone'))
    # Mail specific data
    subject = f"Contact request from {surname} {name}"
    mail_body = f"Name: {name},\nSurname: {surname},\nPhone No.: {phone},\nEmail: {email},\nMessage: {message}"
    # Establish connection to the SMTP server
    server = smtplib.SMTP_SSL(smtp_server, smtp_port)
    # Login to the SMTP server
    server.login(smtp_username, smtp_password)    
    try:
        # Create a test email message
        msg = MIMEText(mail_body)
        msg['Subject'] = subject
        msg['From'] = smtp_username
        msg['To'] = recipient
        # Send the test email
        server.sendmail(smtp_username, recipient, msg.as_string())
        return 'Mail sent succesfully'
    except Exception as e:
         # Capture specific error messages from smtplib exceptions
        error_message = str(e)
        print(f"Error sending email: {error_message}")
        return f'SMTP connection error: {error_message}', 500  # Internal Server Error
    finally:
        # Close the connection to the SMTP server
        if server:
            server.quit()

def send_order_confirmation(order_data):
    email = order_data["billing"]["email"]
    customer_first_name = order_data["billing"]["first_name"]
    subject = f"Nous avons reçu votre commande {customer_first_name}"
    prepared_order_data = prepare_order_data(order_data)
    mail_body = create_order_mail_body(customer_first_name, prepared_order_data)
    # Establish connection to the SMTP server
    server = smtplib.SMTP_SSL(smtp_server, smtp_port)
    # Login to the SMTP server
    server.login(smtp_username, smtp_password)
    try:
        # Create a test email message
        msg = MIMEText(mail_body)
        msg['Subject'] = subject
        msg['From'] = smtp_username
        msg['To'] = email
        bcc_email = ["owais@orbweber.com"]
        recipients = [email] + bcc_email
        # Send the test email
        server.sendmail(smtp_username, recipients, msg.as_string())
        print("send confirmation done")
    except Exception as e:
         # Capture specific error messages from smtplib exceptions
        error_message = str(e)
        print(f"Error sending order email: {error_message}")
    finally:
        # Close the connection to the SMTP server
        if server:
            server.quit()

def create_order_mail_body(customer_first_name, prepared_data):
    greetings = f"Bonjour {customer_first_name},\n\nNous vous remercions d'avoir passé commande sur Greek Meantime!\n\n"
    order_no_sentence = f"Votre commande a bien été reçue et est en cours de traitement. Voici un récapitulatif de votre commande :\n\n"
    order_no_date = f"Numéro de commande : {prepared_data['order_no']}\nDate de commande : {prepared_data['order_date']}\n\n"
    order_details_head = f"Détails de la commande :\n\n"
    order_details_string = f"{prepared_data['order_details']}"
    shipping_method_string = f"Expédition : {prepared_data['shipping_method']}\n\n"
    order_total_string = f"Total : {prepared_data['order_total']}€\n\n"
    shipping_address_head = f"Votre commande sera expédiée à l'adresse suivante :\n"
    shipping_details = f"{prepared_data['shipping_name']}, {prepared_data['shipping_last_name']}\n{prepared_data['address']}\n{prepared_data['city']}, {prepared_data['postcode']}\nFrance\n\n"
    end_greetings = "Vous recevrez un e-mail de confirmation d'expédition dès que votre commande quittera notre entrepôt. Vous pourrez alors suivre l'acheminement de votre colis grâce au numéro de suivi qui vous sera fourni.\n\nSi vous avez des questions ou besoin d'assistance, n'hésitez pas à contacter notre service client à l'adresse someone@gmtimestore.com ou par téléphone au 0621569920. Nous nous ferons un plaisir de vous aider. \n\nNous vous remercions encore pour votre achat et espérons que vous apprécierez vos produits.\n\n"
    signing = "\n\nCordialement,\n\nL'équipe GreekMeanTime\nsomeone@gmtimestore.com\n0621569920\ngmtimestore.com\n\n"
    note =  "Note : Cet e-mail est généré automatiquement, merci de ne pas y répondre directement.\n\n"
    company_details = "Greek Meantime\n118-130 Avenue Jean Jaurès\n75019\nParis\nFrance\n\n"
    precautions = "Vous avez reçu cet e-mail car vous avez effectué une commande sur notre site. Si vous n'êtes pas l'auteur de cette commande, veuillez contacter notre service client immédiatement.\n\nMerci de votre confiance et à bientôt sur gmtimestore.com!"
    mail_body = f"{greetings}{order_no_sentence}{order_no_date}{order_details_head}{order_details_string}{shipping_method_string}{order_total_string}{shipping_address_head}"
    mail_body = f"{mail_body}{shipping_details}{end_greetings}{signing}{note}{company_details}{precautions}"
    return mail_body

def prepare_order_data(order_data):
    order_date_raw = order_data["date_created"]
    dt_object = datetime.fromisoformat(order_date_raw)
    prepared_order_data = {
        "order_no" : order_data["number"],
        "order_date" : dt_object.strftime("%d %B %Y"),
        "order_details" : organize_order_details(order_data["line_items"]),
        "shipping_method" : f"{order_data['shipping_lines'][0]['method_title']} - {order_data['shipping_lines'][0]['total']}€",
        "order_total" : order_data["total"],
        "shipping_name" : order_data["shipping"]["first_name"],
        "shipping_last_name" : order_data["shipping"]["last_name"],
        "address" : f"{order_data['shipping']['address_1']}\n{order_data['shipping']['address_2']}",
        "city" : order_data["shipping"]["city"],
        "postcode" : order_data["shipping"]["postcode"]    
    }
    return prepared_order_data
    
def organize_order_details(order_items):
    order_details = ""
    for item in order_items:
        name = item["name"]
        quantity = item["quantity"]
        subtotal_ref = item["subtotal"]
        order_details = f"{order_details} - {name} x {quantity} - {subtotal_ref}€\n"
    return order_details
