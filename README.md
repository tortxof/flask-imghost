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

#### `/api/collections`

##### GET

Returns a list of collections.

##### POST

Create a new collection.

Parameters:

name
: A unique name used to identify the collecion.

#### `/api/collections/<name>`

##### GET

Get a specific collection. The returned collection object also contains the
associated images.

##### DELETE

Delete a collecion.

#### `/api/images`

##### GET

Returns a list of images.

##### POST

Create a new image.

Parameters:

s3_key
: The S3 key of the image.

s3_bucket
: The S3 bucket where the image is stored.

title (optional)
: A title for the image.

description (optional)
: A description of the image.

#### `/api/images/<s3_key`

##### GET

Get a specific image.

##### PUT

Update an image.

Parameters:

title (optional)
: A title for the image.

description (optional)
: A description of the image.

##### DELETE

Delete an image.
