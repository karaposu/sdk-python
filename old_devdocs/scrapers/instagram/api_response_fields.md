# Instagram API Response Fields

Reference for actual JSON field names returned by Bright Data Instagram API.

---

## Posts (by URL)

**Endpoint:** `client.scrape.instagram.posts(url)`
**Dataset ID:** `gd_lk5ns7kz21pck8jpis`

```json
{
  "url": "https://www.instagram.com/p/DTGAZJQkg5k/",
  "post_id": "3802728663289564772",
  "shortcode": "DTGAZJQkg5k",
  "content_id": "DTGAZJQkg5k",
  "pk": "3802728663289564772",
  "content_type": "Image",

  "user_posted": "harrypotter",
  "user_posted_id": "1315934698",
  "profile_url": "https://www.instagram.com/harrypotter",
  "profile_image_link": "https://...",
  "followers": 12993751,
  "posts_count": 5892,
  "is_verified": true,

  "description": "time for us to embrace the inevitable 😔",
  "alt_text": "Photo by Harry Potter on January 04, 2026...",
  "date_posted": "2026-01-04T15:30:16.000Z",
  "timestamp": "2026-01-15T09:57:02.671Z",

  "likes": 40470,
  "num_comments": 60,

  "photos": ["https://..."],
  "photos_number": 0,
  "thumbnail": "https://...",
  "images": [],
  "videos_duration": null,
  "audio": null,

  "post_content": [
    {
      "index": 0,
      "type": "Photo",
      "url": "https://...",
      "id": "3802728663289564772",
      "alt_text": "..."
    }
  ],

  "latest_comments": [
    {
      "comments": "😂😂😂",
      "user_commenting": "username",
      "likes": 0,
      "profile_picture": "https://..."
    }
  ],

  "is_paid_partnership": false,
  "partnership_details": null,

  "input": {
    "url": "https://www.instagram.com/p/DTGAZJQkg5k/"
  }
}
```

### Field Mapping (Common Names → API Names)

| Common Name | API Field |
|-------------|-----------|
| id | `post_id` |
| caption | `description` |
| likes_count | `likes` |
| comments_count | `num_comments` |
| posted_at | `date_posted` |
| username | `user_posted` |
| user_id | `user_posted_id` |

---

## Profiles (by URL)

**Endpoint:** `client.scrape.instagram.profiles(url)`
**Dataset ID:** `gd_l1vikfch901nx3by4`

*TODO: Add actual response fields after testing*

---

## Reels (by URL)

**Endpoint:** `client.scrape.instagram.reels(url)`
**Dataset ID:** `gd_lyclm20il4r5helnj`

```json
{
  "url": "https://www.instagram.com/reel/DTQygzxD6QC/",
  "post_id": "3805763842060821506_1315934698",
  "shortcode": "DTQygzxD6QC",
  "content_id": "DTQygzxD6QC",
  "product_type": "clips",

  "user_posted": "harrypotter",
  "user_profile_url": "https://www.instagram.com/harrypotter",
  "profile_image_link": "https://...",
  "followers": 12993751,
  "following": 0,
  "posts_count": 5892,
  "is_verified": true,

  "description": "physically, we're at our desks...",
  "hashtags": [],
  "date_posted": "2026-01-12T15:00:04.000Z",
  "timestamp": "2026-01-15T10:15:00.000Z",

  "likes": 41422,
  "views": 1234567,
  "video_play_count": 1234567,
  "num_comments": 123,

  "length": 15.5,
  "video_url": "https://...",
  "audio_url": "https://...",
  "thumbnail": "https://...",

  "top_comments": [...],
  "tagged_users": [],
  "coauthor_producers": [],

  "is_paid_partnership": false,
  "partnership_details": null,

  "input": {
    "url": "https://www.instagram.com/reel/DTQygzxD6QC/"
  }
}
```

### Reels Field Mapping (Common Names → API Names)

| Common Name | API Field |
|-------------|-----------|
| id | `post_id` |
| caption | `description` |
| likes_count | `likes` |
| comments_count | `num_comments` |
| views_count | `views` |
| duration | `length` |
| type | `product_type` |
| username | `user_posted` |

---

## Comments (by URL)

**Endpoint:** `client.scrape.instagram.comments(url)`
**Dataset ID:** `gd_ltppn085pokosxh13`

**Note:** Returns a LIST of comments (not a dict).

```json
[
  {
    "url": "https://www.instagram.com/p/DTGAZJQkg5k/",
    "comment_id": "18033726458123456",
    "post_id": "3802728663289564772",
    "post_url": "https://www.instagram.com/p/DTGAZJQkg5k/",
    "post_user": "harrypotter",

    "comment_user": "some_user",
    "comment_user_url": "https://www.instagram.com/some_user",
    "comment": "This is the comment text 😂",
    "comment_date": "2026-01-04T16:30:00.000Z",

    "likes_number": 5,
    "replies_number": 2,

    "timestamp": "2026-01-15T10:30:00.000Z",
    "input": {
      "url": "https://www.instagram.com/p/DTGAZJQkg5k/"
    }
  }
]
```

### Comments Field Mapping (Common Names → API Names)

| Common Name | API Field |
|-------------|-----------|
| id | `comment_id` |
| username | `comment_user` |
| text | `comment` |
| likes_count | `likes_number` |
| replies_count | `replies_number` |
| created_at | `comment_date` |

---

## Discovery: Profiles (by username)

**Endpoint:** `client.search.instagram.profiles(user_name)`
**Dataset ID:** `gd_l1vikfch901nx3by4`
**Extra Params:** `type=discover_new&discover_by=user_name`

```json
{
  "account": "nasa",
  "id": "528817151",
  "fbid": "123456789",
  "full_name": "NASA",
  "profile_name": "NASA",
  "profile_url": "https://www.instagram.com/nasa",
  "profile_image_link": "https://...",

  "followers": 97896265,
  "following": 93,
  "posts_count": 4582,
  "highlights_count": 15,

  "is_verified": true,
  "is_private": false,
  "is_business_account": true,
  "is_professional_account": true,
  "is_joined_recently": false,
  "has_channel": false,

  "biography": "🚀 🌎  Exploring the universe...",
  "bio_hashtags": [],
  "category_name": "Government Organization",
  "business_category_name": "Government Organization",
  "business_address": null,
  "email_address": null,
  "external_url": "https://nasa.gov",
  "external_url_title": "nasa.gov",

  "avg_engagement": 0.0012,
  "post_hashtags": ["nasa", "space", ...],
  "posts": [...],
  "highlights": [...],
  "related_accounts": [...],

  "url": "https://www.instagram.com/nasa",
  "partner_id": null,
  "timestamp": "2026-01-15T10:45:00.000Z",
  "input": { "user_name": "nasa" },
  "discovery_input": { "user_name": "nasa" }
}
```

### Profile Discovery Field Mapping (Common Names → API Names)

| Common Name | API Field |
|-------------|-----------|
| username | `account` |
| name | `full_name` or `profile_name` |
| followers_count | `followers` |
| following_count | `following` |
| bio | `biography` |

---

## Discovery: Posts (by profile URL)

**Endpoint:** `client.search.instagram.posts(url, ...)`
**Dataset ID:** `gd_lk5ns7kz21pck8jpis`
**Extra Params:** `type=discover_new&discover_by=url`

*TODO: Add actual response fields after testing*

---

## Discovery: Reels (by profile URL)

**Endpoint:** `client.search.instagram.reels(url, ...)`
**Dataset ID:** `gd_lyclm20il4r5helnj`
**Extra Params:** `type=discover_new&discover_by=url`

*TODO: Add actual response fields after testing*

---

## Discovery: Reels All (by profile URL)

**Endpoint:** `client.search.instagram.reels_all(url, ...)`
**Dataset ID:** `gd_lyclm20il4r5helnj`
**Extra Params:** `type=discover_new&discover_by=url_all_reels`

*TODO: Add actual response fields after testing*
