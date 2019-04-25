#!/usr/bin/env python

"""
NAME
    sendTo.py - emails test results

SYNOPSIS
    sudo ./sendTo.py
    sudo ./sendTo.py -ip IP
    sudo ./sendTo.py -ip IP -attachment ATTACHMENT

DESCRIPTION
    Creates and sends the results email to the recipients. It gets called by
    pnp.py main script but it can also be run stand-alone.

COPYRIGHT
    2014 Intel Corporation. All Rights Reserved.
"""

import smtplib, os, sys
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import pickle
import pnp_util
import argparse

ipaddr = ""

def send_mail(send_from, send_to, subject, text, files=[]):
    server ='smtp.intel.com'
    assert isinstance(send_to, list)
    assert isinstance(files, list)

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    html = MIMEText(text, 'html')

    msg.attach(html)

    for f in files:
        if f != "":
            part = MIMEBase('application', "octet-stream")
            part.set_payload( open(f,"rb").read() )
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"'
                            % os.path.basename(f))
            msg.attach(part)

    try:
        smtp = smtplib.SMTP(server)
        smtp.sendmail(send_from, send_to, msg.as_string())
        smtp.close()
        print "Successfully sent email"
    except Exception, e:
        print "Error: Unable to send email " + str(e)


def get_mail_details(attachment):
    mail_comp = {}

    if os.path.isfile("saved_test_vars"):
        mail_comp = pnp_util.get_vars_from_file()
        with open("pnp_results.html", 'r') as smtp_file:
            mail_comp["body"] = smtp_file.read()
    else:
        mail_comp["from"] = 'cros-pnp@intel.com'
        mail_comp["title"] = "Power and Performance Test Results:"

        ver = pnp_util.get_dut_version(ipaddr)

        mail_comp["subject"] = mail_comp["title"] + " Chrome Version: " \
                               + ver["chrome"] + " Firmware: " + \
                               ver["firmware"] + " Build: " + \
                               ver["build"] + " Board: " + ver["board"]
        mail_comp["attachment"] = []
        mail_comp["attachment"].insert(0, attachment)
        with open("pnp_results.html", 'r') as smtp_file:
            mail_comp["body"] = smtp_file.read()

    return mail_comp


if __name__ == "__main__":
    aparser = argparse.ArgumentParser(prog='sendTo.py')
    aparser.add_argument('-ip', nargs=1, help='IP address of the DUT')
    aparser.add_argument('-attachment', nargs=1, help='Email attachment file')
    aparser.add_argument("--to_email", help='Email address for sending'\
                         +' results', metavar='e.g <tester>@intel.com')
    args = aparser.parse_args()

    if args.ip:
        ipaddr = args.ip[0]
        if pnp_util.check_ip(args.ip[0]) == False:
            sys.exit()
        elif args.attachment:
            email_details = get_mail_details(args.attachment[0])
        else:
            email_details = get_mail_details("")
    else:
        email_details = get_mail_details("")

    if args.to_email:
        email_details['to'] = args.to_email

    send_mail(email_details["from"], email_details["to"],
              email_details["subject"], email_details["body"],
              email_details["attachment"])
