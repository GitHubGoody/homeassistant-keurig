# Home Assistant Keurig Integration

Keurig has a [line of SMART Coffee Brewers](https://www.keurig.com/lp/smart-family). This integration utilizes the Keurig API to bring the brewer and its available entities into Home Assistant.

The currently supported brewers are:

- K-Supreme Plus Smart
- K-Supreme Smart
- K-Café Smart

## Installation
### [HACS](https://github.com/hacs/integration) (Recommended)
1. Navigate to HACS > Integrations
2. Click the three dots ⋮ in the top-right corner and select Custom repositories
3. Copy/paste https://github.com/dcmeglio/homeassistant-keurig into the Repository field
4. Select Integration as the Category and click ADD
5. Select the newly added Keurig repository and click DOWNLOAD
6. Click Integrations then click the + in the lower right corner and type in Mail and Packages
7. Restart Home Assistant
8. Navigate to Setting > Device & Services > Integration and click ADD INTEGRATION. If the integration does not show up, refresh the Integrations page.
9. Configure the integration by providing your Keurig username and password.

### Manual
1. Download this repository as a ZIP (green button, top right) and unzip the archive
2. Copy the keurig folder inside the custom_components folder to the Home Assistant /<config path>/custom_components/ directory. You may need to create the custom_components in your Home Assistant installation folder if it does not exist from previous custom integration installations.
3. Restart Home Assistant
4. Navigate to Setting > Device & Services > Integration and click ADD INTEGRATION. If the integration does not show up, refresh the Integrations page.
5. Configure the integration by providing your Keurig username and password.

When configured, the Keurig integration will automatically discover the currently supported devices as configured in the Keurig native app. The generic device id (e.g. 'k29') will initially be used for the device name and entity id's, but can be changed as necessary after initial configuration. 

## Known states
<div class='note'>
Keurig's API is not documented, so these lists may be incomplete. Please let @dcmeglio know if you discover additional states.
</div>

### Brewer:
- ready: Ready to brew - Does not necessarily mean there is a pod since you can brew hot water without a pod
- no water: Low/no water - Will not brew unless you add water
- pod not removed: A pod is in the brewer, but it's used
- lid open
- canceling: You've cancelled an in-progress brew
- brewing complete: Only appears occasionally after brewing - Usually the brew goes straight from brewing to pod not removed

### Pod states:
- empty: No pod loaded
- used: Used pod present
- present: New pod loaded
- bad image: The sensor couldn't get a clear image of the pod - Brewer senses a pod, but does not know what it is
