#! /usr/bin/python3

import json
import os
import sys
import urllib

#from botocore.vendored import requests
import requests

disable_post = False

def alertManager(id, subject, am):

  slack = {}
  icon = ':exclamation:'
  slack['color'] = '#44a'
  status = am.pop('status','unknown')

  labels = {}

  for labelKey in ['commonAnnotations', 'commonLabels', 'groupLabels']:
    if labelKey in am.keys():
      labels.update(am[labelKey])

  if 'alerts' in am.keys():
    for alert in am['alerts']:
      slack['author_link'] = alert.pop('generatorURL', None)
      if 'labels' in alert.keys():
        labels.update(alert['labels'])

  if status == 'resolved':
    icon = ':heavy_check_mark:'
    slack['color'] = 'good'
    if 'alertname' in labels.keys():
      slack['author_name'] = '{}: {}'.format(status.title(), labels['alertname'])

  elif 'severity' in labels.keys():

    if 'alertname' in labels.keys() and labels['alertname'] == "Watchdog":
      slack['severity'] = 'drop'
    else:
      slack['severity'] = labels['severity']

    slack['author_name'] = '{}: {} ({})'.format(labels['severity'].title(), labels['alertname'], status.title())

    if labels['severity'] == 'critical':
      icon = ':boom:'
      slack['color'] = 'danger'
    elif labels['severity'] == 'warning':
      icon = ':warning:'
      slack['color'] = 'warning'

  slack['title_link'] = labels.pop('runbook_url', None)
  if subject:
    slack['title'] = subject
  elif 'message' in labels.keys():
    slack['title'] = labels.pop('message')
  elif 'summary' in labels.keys():
    slack['title'] = labels.pop('summary')
  else:
    slack['title'] = None

  if os.getenv('EXTERNAL_URL'):
    slack['text'] = '<{}/#/alerts?silenced=false&inhibited=false&active=true&filter={} |{} Alertmanager: {}>'.format(os.getenv('EXTERNAL_URL'), urllib.parse.quote(am['groupKey'][3:].replace("\\", "")), icon, id )
  elif 'externalURL' in am.keys():
    slack['text'] = '<{}/#/alerts?silenced=false&inhibited=false&active=true&filter={} |{} Alertmanager: {}>'.format(am['externalURL'], urllib.parse.quote(am['groupKey'][3:].replace("\\", "")), icon, id )
  else:
    slack['text'] = '{} Alertmanager: {}'.format(icon, id)

  if len(labels):
    if 'summary' in labels.keys():
      slack['text'] = "{}\n{}".format(slack['text'], labels.pop('summary'))
    if 'description' in labels.keys():
      slack['text'] = "{}\n{}".format(slack['text'], labels.pop('description'))
    slack['text'] = "{}{}".format(slack['text'], json.dumps(labels, sort_keys = False, indent = 2)[1:-1].replace('"', '').replace(',$', ''))
  else:
    slack['text'] = "{}{}".format(slack['text'], json.dumps(am, sort_keys = False, indent = 2))

  slack['fallback'] = '{}: {}'.format(status.title(), labels.pop('alertname',slack['title']))

  return slack


def cloudwatch(id, subject, cw):

  slack = {}
  icon = ':exclamation:'
  slack['color'] = '#44a'
  status = cw.pop('NewStateValue','unknown')

  if status == 'ALARM':
    icon = ':boom:'
    slack['color'] = 'danger'

  slack['author_name'] = '{}: {}'.format(status.title(), cw.pop('AlarmName', 'Cloud Watch Alarm'))
  slack['title'] = cw.pop('AlarmDescription', None)
  slack['text'] = '{}\nAlarnArn: {}'.format(cw.pop('NewStateReason', None),cw.pop('AlarmArn', None))

  slack['fallback'] = '{}: {}'.format(status.title(), slack['title'])

  return slack


def procRec(r):

  id = r['Sns']['MessageId']
  subject = r['Sns']['Subject']
  msg = r['Sns']['Message']

  try:
    j = json.loads(msg)
    if 'AlarmArn' in j.keys():
      return cloudwatch(id, subject, j)
    else:
    # if message is json and has no AlarmArm assume it came from AlertManager
      return alertManager(id, subject, j)

  except ValueError as e:
    slack = {}
    slack['author_name'] = id
    slack['title'] = subject
    slack['text'] = msg.replace('\\n','\n')
    return slack


def handler(event, context):
  CHANNEL  = os.getenv('CHANNEL')
  USERNAME  = os.getenv('USERNAME')
  WEBHOOK  = os.getenv('WEBHOOK')

  if CHANNEL is None:
    print("Environment Variable CHANNEL not defined.")
    return;

  if USERNAME is None:
    print("Environment Variable USERNAME not defined.")
    return;

  if WEBHOOK is None:
    print("Environment Variable WEBHOOK not defined.")
    return;

  print('event: %s' % json.dumps(event))

  data = {
    'channel': CHANNEL,
    'username': USERNAME,
    'attachments': []
  }

  if 'Records' in event:
    for r in event['Records']:
      slack = procRec(r)
      if slack.pop('severity', 'undefined') != 'drop':
        data['attachments'].append(slack)
      else:
        print('drop: %s' % json.dumps(slack))
  else:
    slack = {}
    slack['text'] =  json.dumps(event, sort_keys = False, indent = 2)
    slack['title'] =  "SNS Notification: Unknown format"
    slack['fallback'] = slack['title']
    data['attachments'].append(slack)

  if len(data['attachments']):
    print('sent: %s' % json.dumps(data))
    if not disable_post:
      r = requests.post(WEBHOOK, json = data)
      print('result: %d' % r.status_code)


if __name__ == "__main__":
  disable_post = True
  d = json.load(sys.stdin)
# print(json.dumps(d))
  handler(d, None)
