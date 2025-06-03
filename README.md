# Home Assistant Email Notifier
**Sending email notifications from Home Assistant.**

The Email Notifier is an integration for Home Assistant allowing you to send email messages, notifications or alerts to any email recipient. The Email Notifier is based on the Home Assistant SMTP integration, but has a user interface for the email server configuration.
<br />
<br />

## Features
- Send Home Assistant alerts, notifications and messages to email recipient(s).
- UI-based configuration for easy setup.
- Backward compatibility with YAML configuration.
- Supports sending messages to multiple recipients.
- Options flow to update configurations without reinstallation.
- Detailed error handling and logging for troubleshooting.
<br />

## Installation

### HACS (recommended)
<!--<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=microteq&amp;repository=whatsigram_messenger&amp;category=integration" target="_blank" rel="noreferrer noopener"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and open a repository inside the Home Assistant Community Store."></a>-->

<!--[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=microteq&repository=whatsigram_messenger)-->

This is the recommended installation method.

- Search for and install the Email Notifier integration from HACS
- Restart Home Assistant

### Manual
- Download the latest release.
- Copy the contents of custom_components into the /config/custom_components directory of your Home Assistant installation.
- Restart Home Assistant.
<br>

## Configuration

In your Home Assistant go to _Settings_ > _Devices & services_ and click on _Add integration_. In the search field, search for _email_ and select the integration. This will add an email account entity, you can use to send email notifications from. Fill in the needed information of your mail server. 

### Configuration fields

#### SMTP Server
SMTP server which is used to send the notifications.

#### Port (default: 587)
The port that the SMTP server is using.

#### Username
Username for the SMTP account.

#### Password
Password for the SMTP server that belongs to the given username. 

#### Sender Email
Email address of the sender.

#### Recipient Email(s)
Default email address of the recipient of the notification. This can be a recipient address or a comma delimited list of addresses for multiple recipients.
This is where you want to send your email notifications by default (when not specifying recipients in the action). Any email address(es) specified in the action’s recipient field will override this recipient content.

#### Sender name
Sets a custom ‘sender name’ in the emails headers.

#### Encryption (default: starttls)
Set mode for encryption, starttls, tls or none.

#### Timeout (default: 15)
The timeout in seconds that the SMTP server is using.
<br>
<br>

### Google Mail
Google has some extra layers of protection that need special attention. You must use an **application-specific** password in your notification configuration.

If any of the following conditions are met you will not be able to create an app password:

- You do not have 2-step verification enabled on your account.
- You have 2-step verification enabled but have only added a security key as an authentication mechanism.
- Your Google account is enrolled in Google’s Advanced Protection Program.
- Your Google account belongs to a Google Workspace that has disabled this feature. Accounts owned by a school, business, or other organization are examples of Google Workspace accounts.
<br/>

## Usage

The Email Notifier creates email accounts from which notifications can be sent. Each account also has a default recipient. In Home Assistant, sending a message is typically used as an action in an automation.

### Using the user interface

#### Method A
In your automation, click on _Add action_, then on _Notifications,_ and select the action _Send a notification message_. In the _Message_ field, enter your message, and as _Target_, click on _Choose entity_ and select one (or more) sender email account(s). The recipients(s) will be the default recipients(s) defined in the mail account configuration. Then save your action.

### Writing YAML

```
alias: Send Test Message
description: ""
triggers: []
conditions: []
actions:
  - action: notify.send_message
    data:
      message: "This is a test message from Home Assistant"
    target:
      entity_id: notify.email_notification_sender_1
mode: single
```
<br />

## License

This integration is published under the GNU General Public License v3.0.
<br />
<br/>

## Attribution

The Email Notifier is based on the Home Assistant SMTP integration.
<br />
<br />
<br />
<br />
<br />
<br />

## About sponsorship

If this Home Assistant integration is helpful to you, please consider supporting this project. Sponsorship helps keep the project going, improve features, and fix any issues that arise. Your contribution goes a long way in making the project better for everyone.


[![Sponsor me on GitHub](https://img.shields.io/badge/sponsor-me%20on%20GitHub-green)](https://github.com/sponsors/microteq)

<a href="https://www.buymeacoffee.com/microteq" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="140" height="38" style="height: 38px !important;width: 140px !important;" ></a>








