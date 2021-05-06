import json
import os
import urllib

#from botocore.vendored import requests
import requests

def alertManager(id, am):

    slack = {}
    icon = ':exclamation:'
    slack['color'] = '#44a'

    labels = {}

    for labelKey in ['commonAnnotations', 'commonLabels', 'groupLabels']:
      if labelKey in am.keys():
        labels.update(am[labelKey])

    if 'alerts' in am.keys():
      for alert in am['alerts']:
        slack['author_link'] = alert.pop('generatorURL', None)
        if 'labels' in alert.keys():
          labels.update(alert['labels'])

    if am['status'] == 'resolved':
      icon = ':heavy_check_mark:'
      slack['color'] = 'good'
      if 'alertname' in labels.keys():
        slack['author_name'] = '{}: {}'.format(am['status'].title(), labels['alertname'])

    elif 'severity' in labels.keys():

      if 'alertname' in labels.keys() and labels['alertname'] == "Watchdog":
        slack['severity'] = 'drop'
      else:
        slack['severity'] = labels['severity']

      slack['author_name'] = '{}: {} ({})'.format(labels['severity'].title(), labels['alertname'], am['status'].title())

      if labels['severity'] == 'critical':
        icon = ':boom:'
        slack['color'] = 'danger'
      elif labels['severity'] == 'warning':
        icon = ':warning:'
        slack['color'] = 'warning'

    slack['title_link'] = labels.pop('runbook_url', None)
    if 'message' in labels.keys():
        slack['title'] = labels.pop('message')
    elif 'summary' in labels.keys():
        slack['title'] = labels.pop('summary')
    
    externalURL = os.getenv('EXTERNAL_URL')
    if externalURL is None:
      externalURL = am['externalURL']

    slack['text'] = '<{}/#/alerts?silenced=false&inhibited=false&active=true&filter={} |{} Alertmanager: {}>'.format(externalURL, urllib.parse.quote(am['groupKey'][3:].replace("\\", "")), icon, id )

    if 'summary' in labels.keys():
      slack['text'] = "{}\n{}".format(slack['text'], labels.pop('summary'))
    if 'description' in labels.keys():
      slack['text'] = "{}\n{}".format(slack['text'], labels.pop('description'))

    if len(labels):
      slack['text'] = "{}{}".format(slack['text'], json.dumps(labels, sort_keys = False, indent = 2)[1:-1].replace('"', '').replace(',$', ''))

    slack['fallback'] = '{}: {}'.format(am['status'].title(), labels['alertname'])

    return slack


def procRec(r):

  msg = r['Sns']['Message']

  try:
    am = json.loads(msg) # if message is json assume it came from AlertManager
    return alertManager(r['Sns']['MessageId'], am)

  except ValueError as e:
    slack = {}
    slack['author_name'] = r['Sns']['MessageId']
    slack['title'] = r['Sns']['Subject']
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
    r = requests.post(WEBHOOK, json = data)
    print('result: %d' % r.status_code)
