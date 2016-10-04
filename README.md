# flask-imghost

A flask based image hosting service.

## API

The app exposes a read-only public API and a private API with endpoints for
individual images and collections of images. All collection names share a common
namespace.

### Public Resources

#### `/api/c/<collection_name>`

Returns a JSON object with the name of the collection and a list of images in
the collection.

Example: `/api/c/my_collection`

```json
{
  "type": "collection",
  "name": "my_collection",
  "images": [
    {},
    {}
  ]
}
```

#### `/api/i/<s3_key>`

Returns a JSON object with a single image.

Example: `/api/i/01V9PaTx/my_image.jpg`

```json
{
  "type": "image",
  "url": "https://s3.amazonaws.com/my_bucket/01V9PaTx/my_image.jpg",
  "s3_key": "01V9PaTx/my_image.jpg",
  "title": "Image Title",
  "description": "A description of the image.",
  "size": {"width": 1920, "height": 1080},
  "colors": ["#ffffff"],
  "thumbs": [
    {
      "size": {"width": 512, "height": 288},
      "url": "https://s3.amazonaws.com/my_bucket/01V9PaTx/t512/my_image.jpg"
    }
  ]
}
```

### Private Resources

All private endpoints require an API key or username and password sent using
HTTP basic auth. When using an API key, send any string as the username, and the
key as the password.

#### `/api/api-keys`

##### GET

Returns a list of API keys.

##### POST

Create a new API key.

Parameters:

description (optional)
: A text description of the key. Use to indicate where this key is used.
Defaults to an empty string.

#### `/api/api-keys/<key>`

##### GET

Get a specific API key.

##### PUT

Update an existing API key.

Parameters:

description
: A text description of the key. Use to indicate where this key is used.
Defaults to an empty string.

##### DELETE

Delete an API key.

#### `GET /api/collections`

Returns a list of collections.

#### `GET /api/collections/{collection_name}`

Get a specific collection.

#### `POST /api/collection/{collection_name}`

Creates a new collection.

Request:

```json
{
  "name": "<collection name>"
}
```

Response:

If collection is created successfully, returns a collection object.

Errors:

- 400: Bad collection name.
- 401: Bad API key.
- 409: Collection already exists.

#### `PUT /api/collection/<collection name>`

Add images to a collection.

Request:

```json
{
  "name": "<collection name>",
  "images": [
    "<image S3 key>"
  ]
}
```

Response:

If all images are successfully added, returns a collection object.
