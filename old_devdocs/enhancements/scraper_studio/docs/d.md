> ## Documentation Index
> Fetch the complete documentation index at: https://docs.brightdata.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Develop a Self-Managed Scraper with the IDE

> Learn how to create a self-managed data scraper using the Scraper Studio IDE. Follow steps to write interaction and parser code, preview, save, and initiate your custom scraper.

To develop a custom scraper using our Integrated development environment (IDE), you will need to insert an URL and start interacting with the development environment using Javascript language.

<Steps>
  <Step title="Start from scratch/choose a template">
    You can start from scratch or use a code template to get started with the development.
  </Step>

  <Step title="Write the interaction code">
    Using the interaction code window, you can interact with the elements of the target website.
  </Step>

  <Step title="Write the Parser code">
    Parse the HTML results you gathered from the interaction window.
  </Step>

  <Step title="Run Preview">
    Preview your interaction and collection flow. To test your code, click the play icon.
  </Step>

  <Step title="Save your code">
    Save and complete your own data scraper once you've finished editing.
  </Step>

  <Step title="Set your delivery preference">
    Set up your preferred [delivery settings](/datasets/functions/initiate-collection-and-delivery-options#delivery-options).
  </Step>

  <Step title="Initiate the scraper run">
    [Initiate your scraper](/datasets/functions/initiate-collection-and-delivery-options#initiate-scraper) and get collection results.
  </Step>
</Steps>

Create a Data scraper by writing code in the IDE. The development environment provides all the tools you need to create your own data scraper.



> ## Documentation Index
> Fetch the complete documentation index at: https://docs.brightdata.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Initiate Data Collection & Delivery with IDE Scraper

> Learn how to initiate data collection and set up delivery options using the IDE Scraper. Explore manual, API, and scheduled methods for efficient data scraping.

When writing a scraper code on the IDE, the system auto-saves the scraper as a draft to the development environment. From inside the IDE, you can run one page at a time to sample how your scraper will behave. To get a full production run, you need to save scraper to production by clicking the 'Save to production' button at the top right corner of the IDE screen. All scrapers will appear under the **My scrapers** tab in the control panel. Any inactive scraper will be shown in a faded state.

<Frame>
    <img src="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/my-scrapers.png?fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=9e15b58693b5b900307378dfa344a78c" alt="" data-og-width="1317" width="1317" data-og-height="831" height="831" data-path="images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/my-scrapers.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/my-scrapers.png?w=280&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=1c570749fb2f5c21d2332b787f787a0d 280w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/my-scrapers.png?w=560&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=e8afde80884919904a039e90f034dc09 560w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/my-scrapers.png?w=840&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=1aa974ca81ebf0c4173395135093d227 840w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/my-scrapers.png?w=1100&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=47b00eb0ee1ebe47250df63cbce95658 1100w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/my-scrapers.png?w=1650&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=efec6e2e123c642af704f51602ebbf0c 1650w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/my-scrapers.png?w=2500&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=2db3e09267dde6653353a800b0289b5e 2500w" />
</Frame>

## Initiate scraper

To start collecting the data, choose one of three options:

<Tabs>
  <Tab title="Initiate by API">
    Start data collection through our API without needing to access the Bright Data control panel : [Getting started with API documentation](/api-reference/scraper-studio-api/Getting_started_wtih_the_API)

    Before initiating an API request, Create an API key. **To create an API key, go to:**\
    [Dashboard side menu settings > account settings > API key](https://brightdata.com/cp/setting)

    <Frame>
            <img src="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-by-api.png?fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=cfa88b89067509c7d2556d406829bb12" alt="" data-og-width="1712" width="1712" data-og-height="453" height="453" data-path="images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-by-api.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-by-api.png?w=280&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=7db15b08884b79e679542ad8d59e8f20 280w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-by-api.png?w=560&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=3b986a3abf3f0f1fa819a447e05a74bd 560w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-by-api.png?w=840&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=af0ca9b579229bf39043e0e51e1e0793 840w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-by-api.png?w=1100&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=b8d494af7de313dd190b0d3311ed9265 1100w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-by-api.png?w=1650&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=61744c024bb25f8e30d68ceaca829412 1650w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-by-api.png?w=2500&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=52232675404b32a52846c323f277fd95 2500w" />
    </Frame>

    1. **Set Up Inputs Manually** - provide input manually or through the API request
    2. **Trigger behavior** - you can add several requests in parallel that are activated according to the order they're defined. You can add another job run to the queue and run more than two jobs simultaneously.
    3. **Preview of the API Request** - Bright Data provides you with a REST API call to initiate the scraper. Please select the "Linux Bash" viewer for CURL commands. As soon as you send the request, you will receive a job id.

    You will receive the data according to the delivery preferences defined earlier.

    <Note>
      Receive data API call is required in order to receive data when delivery preferences is set to API download
    </Note>
  </Tab>

  <Tab title="Initiate manually">
    Bright Data's control panel makes it easy to get started collecting data.

    <Frame>
            <img src="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-manually.png?fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=4f2270461d5e2b503ff1513b3af4d6bb" alt="" data-og-width="1718" width="1718" data-og-height="515" height="515" data-path="images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-manually.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-manually.png?w=280&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=a822b1360269f10bf906062e8443f79c 280w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-manually.png?w=560&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=996b4d3d34efa0fe4298163002896656 560w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-manually.png?w=840&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=4de6f56ee6ebf417d07ba2c0fe8eeb54 840w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-manually.png?w=1100&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=1dd455b74e5fcd450a263a8881fb587c 1100w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-manually.png?w=1650&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=b040ec0157aff11cedfb21624b0fe7bc 1650w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-manually.png?w=2500&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=2035e2243b4013d5775c839349d5ec0f 2500w" />
    </Frame>

    1. **Trigger behavior** - you can add several requests in parallel that are activated according to the order they're defined. You can add another job run to the queue and run more than two jobs simultaneously.
    2. **Set up inputs manually**
    3. **Upload CSV file** - If you'd like to add a large amount of input, the easiest way is to add them to a CSV file and upload it to the system. For example, a list of URLs.\
       See the example provided for reference.
  </Tab>

  <Tab title="Schedule a scraper">
    Choose when to initiate the scraper.

    **Step One:**

    1. Choose a date and time for the scraper to start.
    2. Select the frequency it will run (hourly, daily, weekly, etc.)
    3. Set a deadline for when a scraper is complete.
    4. Review your setup.

    <Frame>
            <img src="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/schedule-configuration.png?fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=8ff98514169433ce6b70e810786a063d" alt="" data-og-width="1738" width="1738" data-og-height="908" height="908" data-path="images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/schedule-configuration.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/schedule-configuration.png?w=280&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=bfcfcb2adf4c402bc45040a137dbadea 280w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/schedule-configuration.png?w=560&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=c725ffd55ac6c1809e014595edea3145 560w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/schedule-configuration.png?w=840&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=33e43b3c86c9706f558d7e458f1d85a2 840w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/schedule-configuration.png?w=1100&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=544b57ffc22a7fa0e349757ac5fdeb9b 1100w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/schedule-configuration.png?w=1650&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=c23d753e45717711696761af576e60fe 1650w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/schedule-configuration.png?w=2500&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=c6d39d3dc2eade59bfe239164bd76491 2500w" />
    </Frame>

    **Step Two :**

    1. Add a large number of inputs to a CSV file. For instance, a list of URLs. To upload easily without errors, you can download a template of a CSV structure example.
    2. Set up Inputs manually

    <Frame>
            <img src="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/enter-input.png?fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=fc5ef217b959819e9803129824e37113" alt="" data-og-width="1735" width="1735" data-og-height="912" height="912" data-path="images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/enter-input.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/enter-input.png?w=280&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=f7cb5de8d30adff68a1207c05c14d1c1 280w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/enter-input.png?w=560&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=0a78b00ba8ea33bf4969bf15a0fac8e0 560w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/enter-input.png?w=840&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=fd7bd4c17c664b0be258506ad9ef106c 840w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/enter-input.png?w=1100&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=b8987f4f8232f2c0d3c6ec107ad36f44 1100w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/enter-input.png?w=1650&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=8a1534cdeae0bd475f02a2cee81425de 1650w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/enter-input.png?w=2500&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=47ecd9ff49af3a74ff3ec6a52dfdf6ca 2500w" />
    </Frame>
  </Tab>
</Tabs>

***

## Rate Limits & Concurrent Requests

To ensure stable performance and fair usage, Scraper Studio IDE enforces rate limits based on the request type: single-input (real-time) or batch

### **What is the Rate Limit?**

The Scraper Studio IDE supports the following maximum number of concurrent requests:

| Method    | Rate-limit                     |
| :-------- | :----------------------------- |
| Batch     | up to 1000 concurrent requests |
| Real-time | no limit                       |

Exceeding the batch request limit will result in the following error response: "Maximum limit of 1000 jobs per collector has been exceeded. Please reduce the number of parallel jobs...’

## Batch vs. Real-time Collection Methods

**Batch collection** is designed for large-scale data collection. It lets you submit a list of URLs (or inputs) and retrieve the results once the job is complete.

**Real-time collection** is designed for use cases that require immediate results. It lets you submit a single URL (or input) and receive the response in real time.

Both methods are reliable and efficient—they’re simply optimized for different data collection needs.

## Delivery Options

You can set your delivery preferences for the dataset. To do that simply click on the scraper row from the 'My scrapers' tab and then click on 'Delivery preferences'

<AccordionGroup>
  <Accordion title="Choose when to get the data">
    * Batch : an efficient way of managing large amounts of data
      * Split batch : deliver the data in smaller batches as soon as it's ready
    * Real-time : is an ideal way to get a fast response for one request
      * Skip retries : Do not retry when error occurs. Can speed up collection
  </Accordion>

  <Accordion title="Choose file format">
    * JSON
    * NDJSON
    * CSV
    * XLSX
    * PARQUET
  </Accordion>

  <Accordion title="Choose how to receive the data">
    * Email
    * API Download
    * Webhook
    * Cloud storage providers : Amazon S3, Google Cloud Storage, Azure, Alibaba Cloud OSS
    * SFTP/FTP

      <Note>
        Media files cannot be delivered when it's set to Email or API download
      </Note>
  </Accordion>

  <Accordion title="Choose data preferences (batch)">
    * Result and Errors in separate files
    * Result and Errors together in one file
    * Only successful results
    * Only errors
  </Accordion>

  <Accordion title="Define notifications">
    * Notify when the collection is complete
    * Notify success rates
    * Notify when an error occurs
  </Accordion>
</AccordionGroup>

### Output schema

Schema defines the data point structure and how the data will be organized.

You can change the schema structure and modify the data points to suit your needs, re-order, edit, set default values and add additional data to your output configuration.

<img src="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/output-schema.png?fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=23688a07496b17cb34408ca55a5a3a6d" alt="" data-og-width="1600" width="1600" data-og-height="853" height="853" data-path="images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/output-schema.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/output-schema.png?w=280&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=c685a4c2de57ee7894a7bdd0030f2342 280w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/output-schema.png?w=560&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=175eb3a48cf9e00f185fe92624e11501 560w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/output-schema.png?w=840&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=e8fca5262de1b9eb135ff9b71a6866a6 840w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/output-schema.png?w=1100&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=9587649d12cbfa12c3a59c0a24eb382f 1100w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/output-schema.png?w=1650&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=82a2d6d3e8446eb567dd05acfc57e561 1650w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/output-schema.png?w=2500&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=bd59eb0f6972a5a0e1beb48dacee4ce2 2500w" />

|                           |                                                                                      |
| ------------------------- | ------------------------------------------------------------------------------------ |
| **Input / Output schema** | choose the tab you'd like to configure                                               |
| **Custom validation**     | validate the schema                                                                  |
| **Parsed data**           | data points collected by the scraper                                                 |
| **Add new field**         | if you need additional data point, you can add fields and define field name and type |
| **Additional data**       | additional information you can add to the schema (timestamp, screenshot, etc.)       |


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.brightdata.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Initiate Data Collection & Delivery with IDE Scraper

> Learn how to initiate data collection and set up delivery options using the IDE Scraper. Explore manual, API, and scheduled methods for efficient data scraping.

When writing a scraper code on the IDE, the system auto-saves the scraper as a draft to the development environment. From inside the IDE, you can run one page at a time to sample how your scraper will behave. To get a full production run, you need to save scraper to production by clicking the 'Save to production' button at the top right corner of the IDE screen. All scrapers will appear under the **My scrapers** tab in the control panel. Any inactive scraper will be shown in a faded state.

<Frame>
    <img src="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/my-scrapers.png?fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=9e15b58693b5b900307378dfa344a78c" alt="" data-og-width="1317" width="1317" data-og-height="831" height="831" data-path="images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/my-scrapers.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/my-scrapers.png?w=280&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=1c570749fb2f5c21d2332b787f787a0d 280w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/my-scrapers.png?w=560&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=e8afde80884919904a039e90f034dc09 560w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/my-scrapers.png?w=840&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=1aa974ca81ebf0c4173395135093d227 840w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/my-scrapers.png?w=1100&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=47b00eb0ee1ebe47250df63cbce95658 1100w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/my-scrapers.png?w=1650&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=efec6e2e123c642af704f51602ebbf0c 1650w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/my-scrapers.png?w=2500&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=2db3e09267dde6653353a800b0289b5e 2500w" />
</Frame>

## Initiate scraper

To start collecting the data, choose one of three options:

<Tabs>
  <Tab title="Initiate by API">
    Start data collection through our API without needing to access the Bright Data control panel : [Getting started with API documentation](/api-reference/scraper-studio-api/Getting_started_wtih_the_API)

    Before initiating an API request, Create an API key. **To create an API key, go to:**\
    [Dashboard side menu settings > account settings > API key](https://brightdata.com/cp/setting)

    <Frame>
            <img src="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-by-api.png?fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=cfa88b89067509c7d2556d406829bb12" alt="" data-og-width="1712" width="1712" data-og-height="453" height="453" data-path="images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-by-api.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-by-api.png?w=280&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=7db15b08884b79e679542ad8d59e8f20 280w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-by-api.png?w=560&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=3b986a3abf3f0f1fa819a447e05a74bd 560w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-by-api.png?w=840&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=af0ca9b579229bf39043e0e51e1e0793 840w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-by-api.png?w=1100&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=b8d494af7de313dd190b0d3311ed9265 1100w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-by-api.png?w=1650&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=61744c024bb25f8e30d68ceaca829412 1650w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-by-api.png?w=2500&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=52232675404b32a52846c323f277fd95 2500w" />
    </Frame>

    1. **Set Up Inputs Manually** - provide input manually or through the API request
    2. **Trigger behavior** - you can add several requests in parallel that are activated according to the order they're defined. You can add another job run to the queue and run more than two jobs simultaneously.
    3. **Preview of the API Request** - Bright Data provides you with a REST API call to initiate the scraper. Please select the "Linux Bash" viewer for CURL commands. As soon as you send the request, you will receive a job id.

    You will receive the data according to the delivery preferences defined earlier.

    <Note>
      Receive data API call is required in order to receive data when delivery preferences is set to API download
    </Note>
  </Tab>

  <Tab title="Initiate manually">
    Bright Data's control panel makes it easy to get started collecting data.

    <Frame>
            <img src="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-manually.png?fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=4f2270461d5e2b503ff1513b3af4d6bb" alt="" data-og-width="1718" width="1718" data-og-height="515" height="515" data-path="images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-manually.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-manually.png?w=280&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=a822b1360269f10bf906062e8443f79c 280w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-manually.png?w=560&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=996b4d3d34efa0fe4298163002896656 560w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-manually.png?w=840&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=4de6f56ee6ebf417d07ba2c0fe8eeb54 840w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-manually.png?w=1100&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=1dd455b74e5fcd450a263a8881fb587c 1100w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-manually.png?w=1650&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=b040ec0157aff11cedfb21624b0fe7bc 1650w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/initiate-manually.png?w=2500&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=2035e2243b4013d5775c839349d5ec0f 2500w" />
    </Frame>

    1. **Trigger behavior** - you can add several requests in parallel that are activated according to the order they're defined. You can add another job run to the queue and run more than two jobs simultaneously.
    2. **Set up inputs manually**
    3. **Upload CSV file** - If you'd like to add a large amount of input, the easiest way is to add them to a CSV file and upload it to the system. For example, a list of URLs.\
       See the example provided for reference.
  </Tab>

  <Tab title="Schedule a scraper">
    Choose when to initiate the scraper.

    **Step One:**

    1. Choose a date and time for the scraper to start.
    2. Select the frequency it will run (hourly, daily, weekly, etc.)
    3. Set a deadline for when a scraper is complete.
    4. Review your setup.

    <Frame>
            <img src="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/schedule-configuration.png?fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=8ff98514169433ce6b70e810786a063d" alt="" data-og-width="1738" width="1738" data-og-height="908" height="908" data-path="images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/schedule-configuration.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/schedule-configuration.png?w=280&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=bfcfcb2adf4c402bc45040a137dbadea 280w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/schedule-configuration.png?w=560&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=c725ffd55ac6c1809e014595edea3145 560w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/schedule-configuration.png?w=840&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=33e43b3c86c9706f558d7e458f1d85a2 840w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/schedule-configuration.png?w=1100&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=544b57ffc22a7fa0e349757ac5fdeb9b 1100w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/schedule-configuration.png?w=1650&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=c23d753e45717711696761af576e60fe 1650w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/schedule-configuration.png?w=2500&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=c6d39d3dc2eade59bfe239164bd76491 2500w" />
    </Frame>

    **Step Two :**

    1. Add a large number of inputs to a CSV file. For instance, a list of URLs. To upload easily without errors, you can download a template of a CSV structure example.
    2. Set up Inputs manually

    <Frame>
            <img src="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/enter-input.png?fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=fc5ef217b959819e9803129824e37113" alt="" data-og-width="1735" width="1735" data-og-height="912" height="912" data-path="images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/enter-input.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/enter-input.png?w=280&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=f7cb5de8d30adff68a1207c05c14d1c1 280w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/enter-input.png?w=560&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=0a78b00ba8ea33bf4969bf15a0fac8e0 560w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/enter-input.png?w=840&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=fd7bd4c17c664b0be258506ad9ef106c 840w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/enter-input.png?w=1100&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=b8987f4f8232f2c0d3c6ec107ad36f44 1100w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/enter-input.png?w=1650&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=8a1534cdeae0bd475f02a2cee81425de 1650w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/enter-input.png?w=2500&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=47ecd9ff49af3a74ff3ec6a52dfdf6ca 2500w" />
    </Frame>
  </Tab>
</Tabs>

***

## Rate Limits & Concurrent Requests

To ensure stable performance and fair usage, Scraper Studio IDE enforces rate limits based on the request type: single-input (real-time) or batch

### **What is the Rate Limit?**

The Scraper Studio IDE supports the following maximum number of concurrent requests:

| Method    | Rate-limit                     |
| :-------- | :----------------------------- |
| Batch     | up to 1000 concurrent requests |
| Real-time | no limit                       |

Exceeding the batch request limit will result in the following error response: "Maximum limit of 1000 jobs per collector has been exceeded. Please reduce the number of parallel jobs...’

## Batch vs. Real-time Collection Methods

**Batch collection** is designed for large-scale data collection. It lets you submit a list of URLs (or inputs) and retrieve the results once the job is complete.

**Real-time collection** is designed for use cases that require immediate results. It lets you submit a single URL (or input) and receive the response in real time.

Both methods are reliable and efficient—they’re simply optimized for different data collection needs.

## Delivery Options

You can set your delivery preferences for the dataset. To do that simply click on the scraper row from the 'My scrapers' tab and then click on 'Delivery preferences'

<AccordionGroup>
  <Accordion title="Choose when to get the data">
    * Batch : an efficient way of managing large amounts of data
      * Split batch : deliver the data in smaller batches as soon as it's ready
    * Real-time : is an ideal way to get a fast response for one request
      * Skip retries : Do not retry when error occurs. Can speed up collection
  </Accordion>

  <Accordion title="Choose file format">
    * JSON
    * NDJSON
    * CSV
    * XLSX
    * PARQUET
  </Accordion>

  <Accordion title="Choose how to receive the data">
    * Email
    * API Download
    * Webhook
    * Cloud storage providers : Amazon S3, Google Cloud Storage, Azure, Alibaba Cloud OSS
    * SFTP/FTP

      <Note>
        Media files cannot be delivered when it's set to Email or API download
      </Note>
  </Accordion>

  <Accordion title="Choose data preferences (batch)">
    * Result and Errors in separate files
    * Result and Errors together in one file
    * Only successful results
    * Only errors
  </Accordion>

  <Accordion title="Define notifications">
    * Notify when the collection is complete
    * Notify success rates
    * Notify when an error occurs
  </Accordion>
</AccordionGroup>

### Output schema

Schema defines the data point structure and how the data will be organized.

You can change the schema structure and modify the data points to suit your needs, re-order, edit, set default values and add additional data to your output configuration.

<img src="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/output-schema.png?fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=23688a07496b17cb34408ca55a5a3a6d" alt="" data-og-width="1600" width="1600" data-og-height="853" height="853" data-path="images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/output-schema.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/output-schema.png?w=280&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=c685a4c2de57ee7894a7bdd0030f2342 280w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/output-schema.png?w=560&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=175eb3a48cf9e00f185fe92624e11501 560w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/output-schema.png?w=840&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=e8fca5262de1b9eb135ff9b71a6866a6 840w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/output-schema.png?w=1100&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=9587649d12cbfa12c3a59c0a24eb382f 1100w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/output-schema.png?w=1650&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=82a2d6d3e8446eb567dd05acfc57e561 1650w, https://mintcdn.com/brightdata/ilemiSHw8UogZ13k/images/scraping-automation/web-scraping-ide/initiate-collection-and-delivery-options/output-schema.png?w=2500&fit=max&auto=format&n=ilemiSHw8UogZ13k&q=85&s=bd59eb0f6972a5a0e1beb48dacee4ce2 2500w" />

|                           |                                                                                      |
| ------------------------- | ------------------------------------------------------------------------------------ |
| **Input / Output schema** | choose the tab you'd like to configure                                               |
| **Custom validation**     | validate the schema                                                                  |
| **Parsed data**           | data points collected by the scraper                                                 |
| **Add new field**         | if you need additional data point, you can add fields and define field name and type |
| **Additional data**       | additional information you can add to the schema (timestamp, screenshot, etc.)       |
