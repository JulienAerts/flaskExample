# coding: utf8

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

source_address = "aerts.julien.101@gmail.com"
destination_address = "ja.inf3005@gmail.com"
body = "Please note that I'm writing a script to send emails."
subject = "I send mails!"

msg = MIMEMultipart()
msg['Subject'] = subject
msg['From'] = source_address
msg['To'] = destination_address

msg.attach(MIMEText(body, 'plain'))

try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(source_address, "********")
    text = msg.as_string()
    server.sendmail(source_address, destination_address, text)
    server.quit()
except (socket.error, smtplib.SMTPConnectError):  
    pass

