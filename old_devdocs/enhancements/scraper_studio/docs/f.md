> ## Documentation Index
> Fetch the complete documentation index at: https://docs.brightdata.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Best Practices for Scraper Studio IDE

> Learn the best practices for using Scraper Studio IDE, including optimizing performance, handling errors, managing retries, and writing efficient scraper code.

## Missing `dead_page` condition.

When using `navigate` command, a 'dead\_page' condition should be added to check if the page is not found. This will prevent automatic retries. While we automatically handle this when the response status is 404, in some cases, the website may respond with various other status codes:

Here are good and bad practices examples (you can nevigate between them by clicking on the "Bad" "Good" tabs)

<CodeGroup>
  ```js ❌ Bad theme={null}
  try {
    // no need to wait 30sec 'ok-selector' in case of dead_page()
    wait('ok-selector');
  } catch(e) {
    // in this case we can't be sure that the page is real dead
    dead_page('Page doesn\'t exist');
  }
  ```

  ```js ✅ Good theme={null}
  wait('ok-selector, 404-selector');
  if (el_exists('404-selector'))
    dead_page();
  ```
</CodeGroup>

## Minimize amount of requests to the browser

Some interaction commands like click type el\_exists el\_is\_visible wait wait\_visible make real requests to the browser and may increase latency and decrease performance. It is recommended to combine selectors and make a single call instead of multiple calls.

<CodeGroup>
  ```js ❌ Bad theme={null}
  if (!(el_exists('#price1')) || el_exists('#price2')
    || el_exists('#price3') || el_exists('#discount'))
  {
      dead_page('No price found');
  }
  ```

  ```js ✅ Good theme={null}
  if (!el_exists('#price1, #price2, #price3, #discount'))
    dead_page('No price found');
  ```
</CodeGroup>

## Incorrect usage of `rerun_stage()`

When a website has pagination on the page and data from all pages is required, `rerun_stage()` should be called for each page from the root page instead of calling it from each page. This allows the system to parallelize the requests and make the scraper faster.

<CodeGroup>
  ```js ❌ Bad theme={null}
  navigate(input.url);
  let $ = html_load(html());
  let next_page_url = $('.next_page').attr('href');
  rerun_stage({url: next_page_url});
  ```

  ```js ✅ Good theme={null}
  let url = new URL(input.url);
  if (input.page)
      url.searchParams.set('page', input.page);
  navigate(url);
  // The input.page does not exist except on the root page, from which we
  // have already invoked rerun_stage() for each page.
  if (input.page)
      return;

  let $ = html_load(html());
  let total_products = +$('.total_pages').text();
  let total_pages = Math.ceil(total_products / 20);
  total_pages = Math.min(total_pages, 50);

  for (let page=2;page<=total_pages;page++)
      rerun_stage({url: input.url, page});
  ```
</CodeGroup>

## Use `close_popup()` to close popups

Do not spend time waiting for popups to appear. Use `close_popup('popup_selector', 'close_button_selector')` to close popups. A popup can appear at any time, and in most cases, adding a check before each interaction command is not desirable. Bad

<CodeGroup>
  ```js ❌ Bad theme={null}
  navigate('https://example.com');
  try {
    wait_visible('.cky-btn-accept', {timeout: 5000});
    click('.cky-btn-accept');
  } catch(e) {
      console.log('Accept cookies button does not exist, continue');
  }
  ```

  ```js ✅ Good theme={null}
  // it runs in the background and does not affect the performance.
  // We check if the popup is visible before any interaction like
  // click or type.
  close_popup('.cky-btn-accept', '.cky-btn-accept');
  navigate('https://example.com');
  click('.open-product-full-info');
  ```
</CodeGroup>

## Use `wait_for_parser_value()` with `tag_response()`

When using tag\_response command and needing to ensure that request is finished before collecting data from the page, `wait_for_parser_value()` should be used:

<CodeGroup>
  ```js ❌ Bad theme={null}
  tag_response('product', /api\/product/);
  navigate('https://example.com');

  // parser code
  // in this case we can't be sure that the request is finished
  let {product} = parser;
  return product.data;
  ```

  ```js ✅ Good theme={null}
  tag_response('product', /api\/product/);
  navigate('https://example.com');
  wait_for_parser_value('product');

  // parser code
  let {product} = parser;
  return product.data;
  ```

  ```js ✅ Good theme={null}
  tag_response('product', /api\/product/);
  navigate('https://example.com');

  // you can also get the data from the response in interaction
  let product = wait_for_parser_value('product');
  navigate(product.reviews_url);
  tag_html('reviews_html');

  // parser code
  let {product, reviews_html} = parser;
  let $ = html_load(reviews_html);
  let reviews = $('.review').toArray().map(v=>$(v).text());
  return {
    ...product.data,
    reviews,
  }
  ```
</CodeGroup>

## Custom error messages

Avoid using custom error messages when possible. Our system does the best to provide you with the most accurate error messages:

<CodeGroup>
  ```js ❌ Bad theme={null}
  try {
    wait('selector1');
    //some code
    wait('selector2');
    //some code
  } catch(e) {
    throw "Page not loaded properly"
  }
  ```

  ```js ✅ Good theme={null}
  // Crawler error: waiting for selector "selector1" failed: timeout 30000ms exceeded
  wait('selector1');
  //some code
  wait('selector2');
  //some code
  ```

  ```js ✅ Good theme={null}
  if (!el_exists('.product-title'))
      throw new Error('Failed to load product page');
  ```
</CodeGroup>

## Slow website response, increasing timeouts

If the website is not loading properly, it may be due to a poor peer connection. It is advisable to display an error message, and the system will attempt to load the page using a more stable peer session.

<CodeGroup>
  ```js ❌ Bad theme={null}
  // 120 sec to long for waiting
  wait('selector', {timeout: 120000});
  ```

  ```js ✅ Good theme={null}
  wait('selector'); // better to use default timeout (30 sec)
  wait('selector', {timeout: 45000});
  wait('selector', {timeout: 60000});  // 60 sec is ok for slow websites
  ```
</CodeGroup>

## Retry mechanism

The scraper code should be clear and focus solely on the necessary tasks for scraping data. There is no need to attempt to reinvent the wheel. It's better to emphasize issues unrelated to the code and report them in the system.

<CodeGroup>
  ```js ❌ Bad theme={null}
  let counter = input.counter || 5;
  while (counter > 1) {
    try {
      wait('selector' , {timeout: 500});
      click('selector');
      type('selector');
      //some code
      break;
    } catch(e) {
      // not acceptable use rerun_stage to create new session in case of error
      return rerun_stage({...input, counter: --counter});
    }
  }
  ```

  ```js ✅ Good theme={null}
  navigate("https://example.com");
  wait('h1');
  ```
</CodeGroup>

## Avoid using a try-catch block

This facilitates the development of concise and readable code, effectively managing potential 'null' or 'undefined' values without the reliance on a try-catch block.

<CodeGroup>
  ```js ❌ Bad theme={null}
  try {
    const example = obj.prop;
  } catch(e) {}
  ```

  ```js ❌ Bad theme={null}
  // wasting browser time for no reason
  try { wait('selector'); } catch(e){}
  try { wait_network_idle({timeout: 8000}) } catch(e){};
  try { wait_page_idle(); } catch(e) {}
  ```

  ```js ✅ Good theme={null}
  const example = object?.prop;
  const example2 = object.prop ?? undefined
  const example3 = object.prop ? object.prop : undefined
  ```
</CodeGroup>

## Parser code: get values from set of elements

The best practice code employs the more concise and functional toArray() and map() methods instead of the traditional each() loop. This enhances code readability and upholds a declarative style.

<CodeGroup>
  ```js ❌ Bad theme={null}
  const links = [];
  $('.card.product-wrapper').each(function(i, el) {
    links.push({url: $(this).find('h4 a').attr('href')});
  })
  return links;
  ```

  ```js ✅ Good theme={null}
  const links = $('.card.product-wrapper').toArray().map(v=>({
    url: $(v).find('h4 a').attr('href'),
  }));
  ```
</CodeGroup>

## Normalizing text

We added a custom function to cheerio prototype `$(selector).text_sane()` that removes all unnecessary whitespace characters and replaces them with a single space.

<CodeGroup>
  ```js ❌ Bad theme={null}
  $.prototype.clearText = function () {
    return this.text().replace(/\s+/g, ' ').trim();
  }
  ```

  ```js ✅ Good theme={null}
  let name = $('a').text_sane();
  or if you need only numbers
  let value= +$('a').text().replace(/\D+/g, '');
  ```
</CodeGroup>
