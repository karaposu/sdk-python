https://docs.brightdata.com/datasets/functions/scraper-studio-ide-interface


> ## Documentation Index
> Fetch the complete documentation index at: https://docs.brightdata.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Scraper Studio IDE - Interface Reference

> Scraper Studio's IDE is a browser-based JavaScript development environment for building, testing, and debugging custom web scrapers. This page describes all interface components across two areas: the **IDE panel** and the **scraper Dashboard**.

## IDE panel

The IDE panel is where you write and test your scraper code. Each labeled component below corresponds to a section of the IDE interface.

<Frame>
  <img className="block dark:hidden" src="https://mintcdn.com/brightdata/JfrY1EEkkzPGMWUW/images/scraping-automation/web-scraping-ide/get-to-know-the-IDE-interface/ide-interface-light.png?fit=max&auto=format&n=JfrY1EEkkzPGMWUW&q=85&s=67333800858d0cc0eed12b6dac8246d9" alt="Light mode interface" data-og-width="1814" width="1814" data-og-height="872" height="872" data-path="images/scraping-automation/web-scraping-ide/get-to-know-the-IDE-interface/ide-interface-light.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/brightdata/JfrY1EEkkzPGMWUW/images/scraping-automation/web-scraping-ide/get-to-know-the-IDE-interface/ide-interface-light.png?w=280&fit=max&auto=format&n=JfrY1EEkkzPGMWUW&q=85&s=b6fad952f782e1df514d3d28af51781b 280w, https://mintcdn.com/brightdata/JfrY1EEkkzPGMWUW/images/scraping-automation/web-scraping-ide/get-to-know-the-IDE-interface/ide-interface-light.png?w=560&fit=max&auto=format&n=JfrY1EEkkzPGMWUW&q=85&s=4e50d475c4421c3905fd3201a0ac5dd9 560w, https://mintcdn.com/brightdata/JfrY1EEkkzPGMWUW/images/scraping-automation/web-scraping-ide/get-to-know-the-IDE-interface/ide-interface-light.png?w=840&fit=max&auto=format&n=JfrY1EEkkzPGMWUW&q=85&s=d6ae8a77b4c6bee094726bcd8f7baf42 840w, https://mintcdn.com/brightdata/JfrY1EEkkzPGMWUW/images/scraping-automation/web-scraping-ide/get-to-know-the-IDE-interface/ide-interface-light.png?w=1100&fit=max&auto=format&n=JfrY1EEkkzPGMWUW&q=85&s=ea535bf1407629516f75066502704242 1100w, https://mintcdn.com/brightdata/JfrY1EEkkzPGMWUW/images/scraping-automation/web-scraping-ide/get-to-know-the-IDE-interface/ide-interface-light.png?w=1650&fit=max&auto=format&n=JfrY1EEkkzPGMWUW&q=85&s=b5ad4030f91af9d5f11dee0c28831459 1650w, https://mintcdn.com/brightdata/JfrY1EEkkzPGMWUW/images/scraping-automation/web-scraping-ide/get-to-know-the-IDE-interface/ide-interface-light.png?w=2500&fit=max&auto=format&n=JfrY1EEkkzPGMWUW&q=85&s=d3808ec6d52f4c3bd029a65f9a8e6ddb 2500w" />

  <img className="hidden dark:block" src="https://mintcdn.com/brightdata/JfrY1EEkkzPGMWUW/images/scraping-automation/web-scraping-ide/get-to-know-the-IDE-interface/ide-interface-dark.png?fit=max&auto=format&n=JfrY1EEkkzPGMWUW&q=85&s=b2b3ca7c0b16ffa2076497b8a45ea28b" alt="Dark mode interface" data-og-width="1826" width="1826" data-og-height="864" height="864" data-path="images/scraping-automation/web-scraping-ide/get-to-know-the-IDE-interface/ide-interface-dark.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/brightdata/JfrY1EEkkzPGMWUW/images/scraping-automation/web-scraping-ide/get-to-know-the-IDE-interface/ide-interface-dark.png?w=280&fit=max&auto=format&n=JfrY1EEkkzPGMWUW&q=85&s=66c5ff2b159602edd991decf8b4c985a 280w, https://mintcdn.com/brightdata/JfrY1EEkkzPGMWUW/images/scraping-automation/web-scraping-ide/get-to-know-the-IDE-interface/ide-interface-dark.png?w=560&fit=max&auto=format&n=JfrY1EEkkzPGMWUW&q=85&s=2229de1ef8348361331d099cdcc5d3a2 560w, https://mintcdn.com/brightdata/JfrY1EEkkzPGMWUW/images/scraping-automation/web-scraping-ide/get-to-know-the-IDE-interface/ide-interface-dark.png?w=840&fit=max&auto=format&n=JfrY1EEkkzPGMWUW&q=85&s=1b29a6c9ff4d9140eed56ff480770797 840w, https://mintcdn.com/brightdata/JfrY1EEkkzPGMWUW/images/scraping-automation/web-scraping-ide/get-to-know-the-IDE-interface/ide-interface-dark.png?w=1100&fit=max&auto=format&n=JfrY1EEkkzPGMWUW&q=85&s=387b7c0dd808f4df911d2d2368dd2cdb 1100w, https://mintcdn.com/brightdata/JfrY1EEkkzPGMWUW/images/scraping-automation/web-scraping-ide/get-to-know-the-IDE-interface/ide-interface-dark.png?w=1650&fit=max&auto=format&n=JfrY1EEkkzPGMWUW&q=85&s=8a7f7f4a089ed2f8944c03d4b420d7c1 1650w, https://mintcdn.com/brightdata/JfrY1EEkkzPGMWUW/images/scraping-automation/web-scraping-ide/get-to-know-the-IDE-interface/ide-interface-dark.png?w=2500&fit=max&auto=format&n=JfrY1EEkkzPGMWUW&q=85&s=16a7a2cab4ac3d1e0cd6316153e30246 2500w" />
</Frame>

### A - Templates

A library of pre-built scraper code created by Bright Data's engineers, covering common websites and scraping patterns. Templates are starting points and may require adjustments if a target website's structure has changed.

### B - Stages

Stages allow a scraper to operate across multiple steps in sequence. Each stage receives input from the previous one via next\_stage() or run\_stage(). Use stages when scraping requires navigating across multiple page types - for example, collecting URLs from a listing page, then extracting details from each URL.

> See [Functions](https://docs.brightdata.com/datasets/functions/functions) for a full code example.

### C - Functions reference

An in-IDE reference panel listing all available scraping functions with descriptions and usage examples.

> See [Interaction functions](https://docs.brightdata.com/datasets/functions/functions#ide-interaction-code) and [Parser functions](https://docs.brightdata.com/datasets/functions/functions#parser-functions).

### D - Debugging tabs

| Tab                 | Description                                                                                                                                                            |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Input**           | Define input parameters and select an input set to run a preview test                                                                                                  |
| **Output**          | Structured data returned by the scraper after a preview run                                                                                                            |
| **Children**        | Input sets passed to the next stage in a multi-stage scraper                                                                                                           |
| **Run log**         | Full code execution log for the most recent preview                                                                                                                    |
| **Browser network** | Browser-level network activity log (equivalent to DevTools > Network tab)                                                                                              |
| **Last errors**     | The most recent error messages, including error codes and affected inputs (last 1,000 stored)                                                                          |
| **Crawl inspector** | All pages crawled during a batch job, including successes and failures. For multi-stage scrapers, use **Search for children** to view pages generated from each parent |
| **Output schema**   | Field names and data types for the scraper's output. Click **Edit Schema** to modify input or output schema                                                            |

### E - Input

| Control                 | Description                                   |
| ----------------------- | --------------------------------------------- |
| **Add input parameter** | Define a new input parameter by name and type |
| **New input**           | Add a value to an input set for testing       |
| **Preview**             | Run the scraper against a selected input set  |

### F - Settings

| Setting             | Description                                             |
| ------------------- | ------------------------------------------------------- |
| **Worker**          | Select Browser Worker or Code Worker for this scraper   |
| **Error mode**      | Define scraper behavior when an error occurs            |
| **Take screenshot** | Capture screenshots of loaded pages during preview runs |

> See [Worker types](https://docs.brightdata.com/datasets/functions/worker-types) for guidance on choosing between Browser and Code Workers.

### G - Self-Healing Tool

AI-powered code refactor. Accepts plain-language prompts to fix errors or modify input/output fields without manual code editing.

> See [Self-Healing Tool](https://docs.brightdata.com/datasets/functions/self-healing-tool).

### H - Preview

Runs the scraper against the currently selected input set. Results appear in the **Output** debugging tab.

## Scraper Dashboard Menu

The Dashboard lists all your scrapers under **My Scrapers**. Each scraper has an action menu with the following options:

| Action                   | Description                                                               |
| ------------------------ | ------------------------------------------------------------------------- |
| **Initiate manually**    | Start a collection run directly from the UI                               |
| **Initiate by API**      | Trigger a collection programmatically via API                             |
| **Run on schedule**      | Configure a recurring collection - daily, weekly, or at a custom interval |
| **Delivery preferences** | Set the output format and delivery destination for completed jobs         |
| **Code**                 | Open the scraper in the IDE                                               |
| **Tickets**              | View open support tickets for this scraper                                |
| **Report an issue**      | Submit a report for platform, scraper, or data quality issues             |




> ## Documentation Index
> Fetch the complete documentation index at: https://docs.brightdata.com/llms.txt
> Use this file to discover all available pages before exploring further.

# null

Explore essential coding commands and best practices for using the Web Scraper IDE. Learn how to navigate, parse data, interact with elements, and optimize your scraping tasks efficiently.

## Overview

Scraper Studio IDE uses two types of code to build web scrapers:

1. **Interaction Code** - Controls browser automation and navigation
2. **Parser Code** - Extracts and structures data from HTML

Each type uses different technologies and serves different purposes.

## [**​**](https://docs.brightdata.com/datasets/functions/coding-environment#ide-interaction-code)

## IDE Interaction code

### [**​**](https://docs.brightdata.com/datasets/functions/coding-environment#what-it-does)What It Does

Interaction code controls a real browser session to:

* Navigate to URLs
* Wait for elements to load
* Click buttons and links
* Fill out forms
* Scroll pages
* Handle dynamic content (JavaScript-heavy sites)

You can use jQuery-like expressions in interaction code—CSS selector patterns and methods used to find and manipulate HTML elements.

Below you can find all available functions within the Interaction code for writing a scraper using the IDE.

<Note>
  Commands marked with a star **⭐** are proprietary functions developed by Bright Data.
</Note>

### `bad_input`

Mark the scraper input as bad. This will prevent any crawl retries `error_code=bad_input`

```js  theme={null}
bad_input();
bad_input('Missing search term');
```

***

### `blocked`

Mark the page as failed because of the website refusing access (error\_code=blocked)

```js  theme={null}
blocked();
blocked('Login page was shown');
```

***

### ⭐ `bounding_box`

The box of coordinates that describes the area of an element (relative to the page, not the browser viewport). Only the first element matched will be measured

* `selector`: A valid CSS selector for the element

```js  theme={null}
let box = bounding_box('.product-list');
// box == {
//   top: 10,
//   right: 800,
//   bottom: 210,
//   left: 200,
//   x: 200,
//   y: 10,
//   width: 600,
//   height: 200,
// }
```

***

### ⭐ `browser_size`

Returns current browser window size

```js  theme={null}
TBD
```

***

### ⭐ `capture_graphql`

Capture and replay graphql requests with changed variables

* options: Params to control graphql request to capture
  * url
  * payload - matches key-value pairs in the target's request payload. Replace `id` with the actual key name that differentiates endpoints, and provide the corresponding value to identify the specific response you want to capture

<CodeGroup>
  ```js Example #1 theme={null}
  let q = capture_graphql({
      payload: {id: 'ProfileQuery'},
      // you may need to pass url opt as RegExp in case when
      // graphql endpoint is not "*/graphql" which is default value
      // url: /\bgraphql\b/ // default
  });

  navigate('https://example.com');

  let [first_query, first_response] = q.wait_captured();

  collect(first_response.data.profile);

  let second = q.replay({
      variables: {other_id: 2},
  });

  collect(second.data.profile);
  ```

  ```js Example #2 theme={null}
  let q = capture_graphql({
      payload: {id: 'ProfileQuery'},
      // you may need to pass url opt as RegExp in case when
      // graphql endpoint is not "*/graphql" which is default value
      // url: /\bgraphql\b/ // default
  });

  navigate('https://example.com');

  if (!q.is_captured())
      click('#load_more');

  let [first_query, first_response] = q.wait_captured();

  collect(first_response.data.profile);

  let second = q.replay({
      variables: {other_id: 2},
  });

  collect(second.data.profile);
  ```
</CodeGroup>

***

### ⭐ `click`

Click on an element (will wait for the element to appear before clicking on it)

* `selector`: Element selector

```js  theme={null}
click('#show-more');
$('#show-more').click()
// Click the closest match to the passed coordinates
// (relative to the page).
// For example, clicking the center pin in a map
let box = bounding_box('#map')
let center = {x: (box.left+box.right)/2, y: (box.top+box.bottom)/2};
click('.map-pin', {coordinates: center});
```

***

### ⭐ `close_popup`

Popups can appear at any time during a crawl and it's not always clear when you should be waiting for or closing them. Add `close_popup()` at the top of your code to add a background watcher that will close the popup when it appears. If a popup appears multiple times, it will always be closed

* popup selector: A valid CSS selector
* close selector: A valid CSS selector
* options: `click_inside`: selector of parent iframe which contains close button selector

```js  theme={null}
close_popup('.popup', '.popup_close');
close_popup('iframe.with-popup', '.popup_close', {click_inside: 'iframe.with-popup'});
```

***

### `collect`

Adds a line of data to the dataset created by the crawler

**syntax**: `collect(<data_line>[, <validate_fn>]);`

* `data_line`: A object with the fields you want to collect
* `validate_fn`: Optional function to check that the line data is valid

```js  theme={null}
collect({price: data.price});
collect(product, p=>{
    if (!p.title)
        throw new Error('Product is missing a title');
})
```

***

### `console`

Log messages from the interaction code

```js  theme={null}
console.log(1, 'brightdata', [1, 2], {key: value});
console.error(1, 'brightdata', [1, 2], {key: value});
```

***

### `country`

Configure your crawl to run from a specific country **syntax**: `country(<code>);`

* `code`: 2-character ISO country code

```js  theme={null}
country('us');
```

***

### `dead_page`

Mark a page as a dead link so you can filter it from your future collections `error_code=dead_page`

```js  theme={null}
dead_page();
dead_page('Product was removed');
```

***

### ⭐ `detect_block`

Detects a block on the page

* `resource`: An object specifying the resource required for the detection
  * `selector`
* `condition`: An object specifying how the resource should be processed for detection
  * `exists`
  * `has_text`

```js  theme={null}
detect_block({selector: '.foo'}, {exists: true});
detect_block({selector: '.bar'}, {has_text: 'text'});
detect_block({selector: '.baz'}, {has_text: /regex_pattern/});
```

***

### ⭐ `disable_event_listeners`

Stop all event listeners on the page from running. `track_event_listeners()` must have been called first

* `event_types`: Specific event types that should be disabled

```js  theme={null}
disable_event_listeners();
disable_event_listeners(['hover', 'click']);
```

***

### `el_exists`

Check if an element exists on page, and return a boolean accordingly

* `selector`: Valid CSS selector
* `timeout`: Timeout duration to wait for the element to appear on the page

```js  theme={null}
el_exists('#example'); // => true
el_exists('.does_not_exist'); // => false
el_exists('.does_not_exist', 5e3); // => false (after 5 seconds)
```

***

### `el_is_visible`

Check if element is visible on page

* selector: Valid CSS selector
* timeout: Timeout duration to wait for the element to be visible on the page

```js  theme={null}
el_is_visible('#example');
el_is_visible('.is_not_visible', 5e3); // false (after 5 seconds)
```

***

### `embed_html_comment`

Add a comment in the page HTML. Can be used to embed metadata inside HTML snapshots.

* `comment`: Body of the comment

```js  theme={null}
embed_html_comment('trace-id: asdf123');
```

***

### ⭐ `font_exists`

Assert the capability of the browser to render the given font family on the page **syntax**: `font_exists(<font-family>);`

```js  theme={null}
font_exists('Liberation Mono');
```

***

### ⭐ `freeze_page`

Force the page to stop making changes. This can be used to save the page in a particular state so page snapshots that run after crawl won't see a different page state than you see now. This command is experimental. If you see problems, please report them to support

```js  theme={null}
freeze_page();
```

***

### ⭐ `hover`

hover on an element (will wait for the element to appear before hovering on it) **syntax**: `hover(<selector>);`

* `selector`: Element selector

```js  theme={null}
hover('#item');
```

***

### ⭐ `html_capture_options`

Influence the process of the HTML capturing

* `options`: An object which accepts options defining how HTML capturing should be processed
  * `coordinate_attributes`

```js  theme={null}
html_capture_options({
    coordinate_attributes: true,
});
```

***

### `Image`

Collect image data

* `src`: Image URL or data:image URI string

```js  theme={null}
let i = new Image('https://example.com/image.png');
collect({image: i});
```

***

### `input`

Global object available to the interaction code. Provided by trigger input or `next_stage()` calls

```js  theme={null}
navigate(input.url);
```

***

### `job`

Global object available to the interaction code. Provided by trigger input or `next_stage()` calls

```js  theme={null}
let {created} = job;
```

***

### `load_html`

Load html and return Cheerio instance

* `html`: Any HTML string

```js  theme={null}
let $$ = load_html('<p id="p1">p1</p><p id="p2">p2</p>');
collect({data: $$('#p2').text()});
```

***

### ⭐ `load_more`

Scroll to the bottom of a list to trigger loading more items. Useful for lazy-loaded infinite-scroll sites

* `selector`: Selector for the element that contains the lazy-loaded items

```js  theme={null}
load_more(<selector>);
load_more('.search-results');
load_more('.search-results', {children: '.result-item', trigger_selector: '.btn-load-more', timeout: 10000});
```

***

### `load_sitemap`

Read a list of urls from a sitemap xml (supports sitemap indexes, and .gz compressed sitemaps. see examples.)

```js  theme={null}
let {pages} = load_sitemap({url: 'https://example.com/sitemap.xml.gz'});
let {children} = load_sitemap({url: 'https://example.com/sitemap-index.xml'});
```

***

### `location`

Object with info about current location. Available fields: href

```js  theme={null}
navigate('https://example.com');
location.href; // "https://example.com/"
```

***

### Money

Collect price/money data

* `value`: Amount of money
* `currency`: Currency code

```js  theme={null}
let p = new Money(10, 'USD');
collect({product_price: p});
```

***

### ⭐ `mouse_to`

Move the mouse to the specified (x,y) position **syntax**: `mouse_to(<x>, <y>);`

* `x`: Target x position
* `y`: Target y position

```js  theme={null}
mouse_to(0, 0);
```

***

### `navigate`

Navigate the browser to a URL **syntax**: `navigate(<url>);`

* A 404 status code will throw a `dead_page` error by default. Use opt.`allow_status` to override this
* `url`: A URL to navigate to
* `opt`: navigate options (see examples)

```js  theme={null}
navigate(input.url);
navigate('https://example.com');

// waits until DOM content loaded event is fired in the browser
navigate(`url`, {wait_until: 'domcontentloaded'});

// adds a referer to the navigation
navigate(`url`, {referer: `url`});

// the number of milliseconds to wait for. Default is 30000 ms
navigate(`url`, {timeout: 45000});

// Don't throw an error if this URL sends a 404 status code
navigate(`url`, {allow_status: [404]});

// Specify browser width/height
navigate(`url`, {
    fingerprint: {screen: {width: 400, height: 400}},
});
```

***

### `next_stage`

Run the next stage of the crawler with the specified input

* `input`: Input object to pass to the next browser session

```js  theme={null}
next_stage({url: 'http://example.com', page: 1});
```

***

### `parse`

Parse the page data

```js  theme={null}
let page_data = parse();
collect({
    title: page_data.title,
    price: page_data.price,
});
```

***

### `preserve_proxy_session`

Preserve proxy session across children of this page

```js  theme={null}
preserve_proxy_session();
```

***

### ⭐ `press_key`

Type special characters like Enter or Backspace in the currently focused input (usually used after typing something in a search box)

```js  theme={null}
press_key('Enter');
press_key('Backspace');
```

***

### ⭐ `proxy_location`

Configure your crawl to run from a specific location. Unless you need high resolution control over where your crawl is running from, you probably want to use `country(code)` instead

* `configuration`: Object with a desired proxy location, check examples for more info

```js  theme={null}
proxy_location({country: 'us'});

// lat in range: [-85, 85], long in range: [-180, 180]
proxy_location({lat: 37.7749, long: 122.4194});

// radius in km
proxy_location({lat: 37.7749, long: 122.4194, country: 'US', radius: 100});
```

***

### ⭐ `redirect_history`

Returns history of URL redirects since last navigate

```js  theme={null}
navigate('http://google.com');
let redirects = redirect_history();
// returns:
// [
//   'http://google.com',
//   'http://www.google.com',
//   'https://www.google.com/',
// ]
```

***

### `rerun_stage`

Run this stage of the crawler again with new input

```js  theme={null}
rerun_stage({url: 'http://example.com/other-page'});
```

***

### `resolve_url`

Returns the final URL that the given url argument leads to

* `url`: URL string/instance

```js  theme={null}
let {href} = parse().anchor_elem_data;
collect({final_url: resolve_url(href)});
```

***

### `response_headers`

Returns the response headers of the last page load

```js  theme={null}
let headers = response_headers();
console.log('content-type', headers['content-type']);
```

***

### `request`

Make a direct HTTP request

* `url` | `options`: the url to make the request to, or request options (see examples)

```js  theme={null}
let res = request('http://www.example.com');
let res = request({url: 'http://www.example.com', method: 'POST', headers: {'Content-type': 'application/json'}, body: {hello: 'world'}})
```

***

### ⭐ `right_click`

The same as click but use right mouse button instead (will wait for the element to appear before clicking on it) **syntax**: `right_click(<selector>);`

* `selector`: Element selector

```js  theme={null}
right_click('#item');
```

***

### `run_stage`

Run a specific stage of the crawler with a new browser session

* stage: Which stage to run (1 is first stage)
* input: Input object to pass to the next browser session

```js  theme={null}
run_stage(2, {url: 'http://example.com', page: 1});
```

***

### ⭐ `scroll_to`

Scroll the page so that an element is visible.If you're doing this to trigger loading some more elements from a lazy loaded list, use `load_more()`. Defaults to scrolling in a natural way, which may take several seconds. If you want to jump immediatley, use `{immediate: true}` **syntax**: `scroll_to(<selector>);`

* `selector`: Selector of the element you want to scroll to

```js  theme={null}
scroll_to('.author-profile');
scroll_to('top'); // scroll to the top of the page
scroll_to('bottom'); // scroll to the bottom of the page
scroll_to('top', {immediate: true}); // jump to top of page immediately
```

***

### ⭐ `scroll_to_all`

Scroll through the page so that all the elements matching the selector will be visible on screen **syntax**: `scroll_to_all(<selector>);`

* `selector`: Selector of the elements you want to scroll through

```js  theme={null}
scroll_to_all('.author-profiles');
```

***

### ⭐ `select`

Pick a value from a select element **syntax**: `select(<select>, <value>);`

* `selector`: Element selector

```js  theme={null}
select('#country', 'Canada');
```

***

### `set_lines`

An array of lines to add to your dataset at the end of this page crawl. Each call to `set_lines()` will override previous ones, and only the last set of lines will be added into the dataset (tracked per page crawl). This is a good fit when the scraper is set to collect partial on errors. You can keep calling `set_lines()` with the data you gathered so far, and the last call will be used if the page crawl throws an error **syntax**: `set_lines(<data_line>[, <validate_fn>]);`

* `lines`: An array of data lines to add to your final dataset
* `validate_fn`: Optional function to check that the line data is valid (run once per line)

```js  theme={null}
set_lines(products_so_far);
set_lines(products_so_far, i=>{
    if (!i.price)
        throw new Error('Missing price');
});
```

***

### `set_session_cookie`

Sets a cookie with the given cookie data; may overwrite equivalent cookies if they exist

```js  theme={null}
set_session_cookie(`domain`, `name`, `value`);
```

***

### `set_session_headers`

Set extra headers for all the HTTP requests

* `headers`: Object with extra headers in key-value format

```js  theme={null}
set_session_headers({'HEADER_NAME': 'HEADER_VALUE'});
```

***

### ⭐ `solve_captcha`

Solve any captchas shown on the page

```js  theme={null}
solve_captcha();
solve_captcha({type: 'simple', selector: '#image', input: '#input'});
```

***

### `status_code`

Returns the status code of the last page load

```js  theme={null}
collect({status_code: status_code()});
```

***

### ⭐ `tag_all_responses`

Save the responses from all browser request that match

* `field`: The name of the tagged field
* `pattern`: The URL pattern to match
* `options`: Set options.jsonp=true to parse response bodies that are in jsonp format. This will be automatically detected when possible

```js  theme={null}
tag_all_responses(<field>, <pattern>, <options>);
tag_all_responses('resp', /url/, {jsonp: true});
tag_all_responses('resp', /url/, {allow_error: true});
tag_all_responses('profiles', /\/api\/profile/);
navigate('https://example.com/sports');
let profiles = parse().profiles;
for (let profile of profiles)
    collect(profile);
```

***

### ⭐ `tag_download`

Allows to get files downloaded by browser

* `url`: A pattern or a string to match requests against

```js  theme={null}
let SEC = 1000;
let download = tag_download(/example.com\/foo\/bar/);
click('button#download');
let file1 = download.next_file({timeout: 10*SEC});
let file2 = download.next_file({timeout: 20*SEC});
collect({file1, file2});
```

***

### ⭐ `tag_image`

Save the image url from an element

* field: The name of the tagged field
* selector: A valid CSS selector

```js  theme={null}
tag_image(field, selector);
tag_image('image', '#product-image');
```

***

### ⭐ `tag_response`

Save the response data from a browser request **syntax**: `tag_response(<field>, <pattern>, <options>);`

* `name`: The name of the tagged field
* `pattern`: The URL pattern to match
* `options`: Set options.jsonp=true to parse response bodies that are in jsonp format. This will be automatically detected when possible

```js  theme={null}
tag_response('resp', /url/, {jsonp: true});
tag_response('resp', /url/, {allow_error: true});
tag_response('resp', (req, res)=>{
            if (req.url.includes('/api/'))
            {
                let request_body = req.body;
                let request_headers = req.headers;
                let response_body = res.body;
                let response_headers = res.headers;
            }
        });

tag_response('teams', /\/api\/teams/);
navigate('https://example.com/sports');
let teams = parse().teams;
for (let team of teams)
    collect(team);
```

***

### ⭐ `tag_screenshot`

Save a screenshot of the page HTML **syntax**: `tag_screenshot(<field>, <options>);`

* field: The name of the tagged field
* options: Download options (see example)

```js  theme={null}
tag_screenshot('html_screenshot', {filename: 'screen'});
tag_screenshot('view', {full_page: false}); // full_page defaults to true
```

***

### ⭐ `tag_script`

Extract some JSON data saved in a script on the page

* name: The name of the tagged script
* selector: The selector of the script to tag

  ```js  theme={null}
  tag_script(field, selector);
  tag_script('teams', '#preload-data');
  tag_script('ssr_state', '#__SSR_DATA__');
  navigate('https://example.com/');
  collect(parse().ssr_state);
  ```

***

### ⭐ `tag_serp`

Parse the current page as a search engine result page

* `field`: The name of the tagged field
* `type`: Parser type: (e.g. bing, google)

```js  theme={null}
tag_serp('serp_bing_results', 'bing')
tag_serp('serp_google_results', 'google')
```

***

### ⭐ `tag_video`

Save the video url from an element

* `field`: The name of the tagged field
* `selector`: A valid CSS selector
* `opt`: download options (see example)

```js  theme={null}
tag_video(field, selector);
tag_video('video', '#product-video', {download: true});
```

***

### ⭐ `tag_window_field`

Tag a js value from the browser page

* `field`: The path to the relevant data

```js  theme={null}
tag_window_field(field, key);
tag_window_field('initData', '__INIT_DATA__');
```

***

### ⭐ `track_event_listeners`

Start tracking the event listeners that the browser creates. It's needed to run `disable_event_listeners()` later

```js  theme={null}
track_event_listeners();
```

***

### ⭐ `type`

Enter text into an input (will wait for the input to appear before typing)

* `selector`: Element selector
* `text`: Text to enter

```js  theme={null}
type(selector, text);
type('#location', 'New York');

// replacing text in input if it is not empty
type(<selector>, <text>, {replace: true});

// type text to an element with id ending "input-box" (e.g. <input id="c2E57-input-box">)
type('[id$=input-box]', <text>);

// dispatching 'Enter' key press
type(<selector>, ['Enter']);

// typing text and then dispatching 'Enter' key press
type(<selector>, ['Some text', 'Enter']);

// deleting 1 char from input
type(<selector>, ['Backspace']);
```

***

### `URL`

URL class from NodeJS standard "url" module

* `url`: URL string

```js  theme={null}
let u = new URL('https://example.com');
```

***

### ⭐ `verify_requests`

Monitor failed requests with a callback function

* `callback`: A function which will be called on each failed request with an object in format: `{url, error, type, response}`

```js  theme={null}
verify_requests(({url, error, type, response})=>{
    if (response.status!=404 && type=='Font')
        throw new Error('Font failed to load');
});
```

***

### `Video`

Collect video data

* `src`: Video URL

```js  theme={null}
let v = new Video('https://example.com/video.mp4');
collect({video: v});
```

***

### ⭐ `wait`

Wait for an element to appear on the page

* `selector`: Element selector
* `opt`: wait options (see examples)

```js  theme={null}
wait(<selector>);
wait('#welcome-splash');
wait('.search-results .product');
wait('[href^="/product"]');

// the number of milliseconds to wait for. Default is 30000 ms
wait(<selector>, {timeout: 5000});

// wait for element to be hidden
wait(<selector>, {hidden: true});

// wait for element inside in an iframe
wait(<selector>, {inside: '#iframe_id'});
```

***

### ⭐ `wait_any`

Wait for any matching condition to succeed

```js  theme={null}
wait_any(['#title', '#notfound']);
```

***

### `wait_for_parser_value`

Wait for a parser field to contain a value. This can be useful after you click something to wait for some data to appear

* `field`: The parser value path to wait on
* `validate_fn`: An optional callback function to validate that the value is correct
* `opt`: Extra options (e.g. timeout)

```js  theme={null}
wait_for_parser_value(<field>[, <validate_fn>][, opt]);
wait_for_parser_value('profile');
wait_for_parser_value('listings.0.price', v=>{
            return parseInt(v)>0;
        }, {timeout: 5000});
```

***

### ⭐ `wait_for_text`

Wait for an element on the page to include some text

* `selector`: Element selector
* `text`: The text to wait for

```js  theme={null}
wait_for_text(<selector>, <text>);
wait_for_text('.location', 'New York');
```

***

### ⭐ `wait_hidden`

Wait for an element to not be visible on the page (removed or hidden)

* `selector`: Element selector

```js  theme={null}
wait_hidden(<selector>);
wait_hidden('#welcome-splash');
wait_hidden(<selector>, {timeout: 5000});
```

***

### ⭐ `wait_network_idle`

Wait the browser network has been idle for a given time

* `timeout`: Wait for browser network to be idle for X milliseconds
* `options`: ignore: an array of patterns to exclude requests from monitoring timeout: how long the network needs to be idle in milliseconds (default 500)

```js  theme={null}
wait_network_idle();
wait_network_idle({
    timeout: 1e3,
    ignore: [/long_request/, 'https://example.com'],
});
```

***

### ⭐ `wait_page_idle`

Wait until no changes are being made on the DOM tree for a given time

* `timeout`: Milliseconds to wait for no changes
* `options`: An object, which can accept a ignore argument to exclude some elements from monitoring

```js  theme={null}
wait_page_idle();
wait_page_idle({
    ignore: [<selector1>, <selector2>],
    idle_timeout: 1000,
});
```

***

### ⭐ `wait_visible`

Wait for an element to be visible on the page

* `selector`: Element selector

```js  theme={null}
wait_visible(<selector>);
wait_visible('#welcome-splash');
wait_visible(<selector>, {timeout: 5000});
```

***

### `$`

Helper for jQuery-like expressions

* `selector`: Element selector

```js  theme={null}
$(<selector>);
wait($('.store-card'))
```

***

### `Clicking on selector based on text`

Helper for jQuery-like expressions

* `selector`: Element selector

```js  theme={null}
$('.selector').filter_includes('text').click()
```

### ⭐ `emulate_device`

View pages as a mobile device. This command will change user agent and screen parameters (resolution and device pixel ratio)

* `device`: A string with the name of device

```js  theme={null}
emulate_device('iPhone X');
emulate_device('Pixel 2');
```

<Accordion title="Here is the full list of device names">
  * Blackberry PlayBook
  * Blackberry PlayBook landscape
  * BlackBerry Z30
  * BlackBerry Z30 landscape
  * Galaxy Note 3
  * Galaxy Note 3 landscape
  * Galaxy Note II
  * Galaxy Note II landscape
  * Galaxy S III
  * Galaxy S III landscape
  * Galaxy S5
  * Galaxy S5 landscape
  * Galaxy S8
  * Galaxy S8 landscape
  * Galaxy S9+
  * Galaxy S9+ landscape
  * Galaxy Tab S4
  * Galaxy Tab S4 landscape
  * iPad
  * iPad landscape
  * iPad (gen 6)
  * iPad (gen 6) landscape
  * iPad (gen 7)
  * iPad (gen 7) landscape
  * iPad Mini
  * iPad Mini landscape
  * iPad Pro
  * iPad Pro landscape
  * iPad Pro 11
  * iPad Pro 11 landscape
  * iPhone 4
  * iPhone 4 landscape
  * iPhone 5
  * iPhone 5 landscape
  * iPhone 6
  * iPhone 6 landscape
  * iPhone 6 Plus
  * iPhone 6 Plus landscape
  * iPhone 7
  * iPhone 7 landscape
  * iPhone 7 Plus
  * iPhone 7 Plus landscape
  * iPhone 8
  * iPhone 8 landscape
  * iPhone 8 Plus
  * iPhone 8 Plus landscape
  * iPhone SE
  * iPhone SE landscape
  * iPhone X
  * iPhone X landscape
  * iPhone XR
  * iPhone XR landscape
  * iPhone 11
  * iPhone 11 landscape
  * iPhone 11 Pro
  * iPhone 11 Pro landscape
  * iPhone 11 Pro Max
  * iPhone 11 Pro Max landscape
  * iPhone 12
  * iPhone 12 landscape
  * iPhone 12 Pro
  * iPhone 12 Pro landscape
  * iPhone 12 Pro Max
  * iPhone 12 Pro Max landscape
  * iPhone 12 Mini
  * iPhone 12 Mini landscape
  * iPhone 13
  * iPhone 13 landscape
  * iPhone 13 Pro
  * iPhone 13 Pro landscape
  * iPhone 13 Pro Max
  * iPhone 13 Pro Max landscape
  * iPhone 13 Mini
  * iPhone 13 Mini landscape
  * JioPhone 2
  * JioPhone 2 landscape
  * Kindle Fire HDX
  * Kindle Fire HDX landscape
  * LG Optimus L70
  * LG Optimus L70 landscape
  * Microsoft Lumia 550
  * Microsoft Lumia 950
  * Microsoft Lumia 950 landscape
  * Nexus 10
  * Nexus 10 landscape
  * Nexus 4
  * Nexus 4 landscape
  * Nexus 5
  * Nexus 5 landscape
  * Nexus 5X
  * Nexus 5X landscape
  * Nexus 6
  * Nexus 6 landscape
  * Nexus 6P
  * Nexus 6P landscape
  * Nexus 7
  * Nexus 7 landscape
  * Nokia Lumia 520
  * Nokia Lumia 520 landscape
  * Nokia N9
  * Nokia N9 landscape
  * Pixel 2
  * Pixel 2 landscape
  * Pixel 2 XL
  * Pixel 2 XL landscape
  * Pixel 3
  * Pixel 3 landscape
  * Pixel 4
  * Pixel 4 landscape
  * Pixel 4a (5G)
  * Pixel 4a (5G) landscape
  * Pixel 5
  * Pixel 5 landscape
  * Moto G4
  * Moto G4 landscape
</Accordion>

***

## Parser Functions

### Overview

Parser code is responsible for extracting and structuring data from HTML content.

Scraper Studio Parser code uses the pre-installed Cheerio library—a library that provides jQuery-like syntax for parsing HTML documents.

\
Below you can find explanations of the available commands within the Parser code for writing a scraper using the IDE:

### `input`

Global variable available to the parser code

```js  theme={null}
let url = input.url;
```

***

### `$`

An instance of cheerio

```js  theme={null}
$('#example').text();
$('$example').attr('href');
$('#example').text_sane(); /* This is like $().text() but also trims text and replace all space characters with single space "a b \t\n\n c" -> "a b c" */
```

<Tip>
  Find more information on the [cheerio website](https://cheerio.js.org/).
</Tip>

***

### `location`

A global variable available to the parser code that contains information about the current location

```js  theme={null}
let current_url = location.href;
```

***

### `Image`

Collect image data

```js  theme={null}
let i = new Image('https://example.com/image.png');
collect({image: i});
```

***

### `Video`

Collect video data

```js  theme={null}
let v = new Video('https://example.com/video.mp4');
collect({video: v});
```

***

### `Money`

Collect price/money data

```js  theme={null}
let p = new Money(10, 'USD');
collect({product_price: p});
```



> ## Documentation Index
> Fetch the complete documentation index at: https://docs.brightdata.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Worker types

> This article explains the behavior difference between worker types, how to choose the right one for your project

Browser worker and code worker are two technical approaches for scraping, and you should choose between them based on your needs and  technical challenges you're facing with the website you're scraping.

## Browser worker vs Code worker

**Browser Workers:**

* Can simulate a user's interaction with the website via a headless browser
* Handles complex scraping tasks like filling forms, and dynamic content loading.

**Code workers:**

* Roughly equivalent to doing a curl or python `requests.get(url)`
* Work by sending HTTP requests to the target website
* Can only work in situations that don't require interacting with the website UI

## Choose the optimal worker type

Choose the appropriate worker type based on the website's technology and the navigation required to scrape your target data.

**Best practice:** Start with the Code worker type and only switch if you can't extract the data you need.

**When to use Browser worker:**

* You need to click elements to load additional data
* You need to scroll to load more content
* You need to capture network traffic from inside the browser (using `tag_script` or `tag_response`)
* You need to type text to perform searches or trigger dynamic content"

## Align your code with worker type

Some functions in our library are only available when using Browser workers and will throw an error if you try to use them with Code workers.

Below is a list of functions that can only be used with Browser workers:

* `wait_*` (any wait function)
* `scroll_*` (any scroll function)
* `tag_*` (any tag function)
* `type`
* `browser_size`
* `emulate_device`
* `freeze_page`
* `click`
* `hover`
* `right_click`
* `mouse_to`
* `press_key`
* `solve_captcha`
* `capture_graphql`
* `close_popup`
