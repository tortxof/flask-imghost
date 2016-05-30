# flask-imghost

A flask based image hosting service.

## API

The app exposes a read-only public API with endpoints for individual images and
collections of images. All collection names share a common namespace.

### Endpoints

#### `/api/c/<collection>`

Returns a JSON object with the name of the collection and a list of images in
the collection.

Example: `/api/c/my_collection`

```json
{
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
  "url": "https://s3.amazonaws.com/my_bucket/01V9PaTx/my_image.jpg",
  "s3_key": "01V9PaTx/my_image.jpg",
  "title": "Image Title",
  "description": "A description of the image."
}
```
