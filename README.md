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

#### `/api/i/<image>`

Returns a JSON object with a single image.

Example: `/api/i/my_image`

```json
{
  "name": "my_image",
  "url": "https://",
  "type": "image/jpeg",
  "title": "Image Title",
  "description": "A description of the image."
}
```
