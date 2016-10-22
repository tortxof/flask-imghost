import React from 'react'
import _ from 'lodash'

import Nav from './nav'

export default React.createClass({
  createImage(image) {
    fetch('/api/images', {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      credentials: 'same-origin',
      method: 'POST',
      body: JSON.stringify(image)
    })
    .then(response => {
      if (response.status >= 200 && response.status < 300) {
        this.setState(previousState => {
          const uploads = Object.assign({}, previousState.uploads)
          uploads[image.s3_key] = Object.assign(uploads[image.s3_key], {
            message: 'Thumbnails created.',
            state: 'done'
          })
        })
      }
    })
  },
  toggleImageSelect(e) {
    const key = parseInt(e.target.dataset.key)
    let images
    if (e.shiftKey) {
      const idxTo = key
      const idxFrom = idxTo - this.state.images
      .slice(0, idxTo + 1)
      .reverse()
      .map(image => image.selected)
      .indexOf(true)
      const keys = this.state.images
      .slice(idxFrom + 1, idxTo + 1)
      .map(image => image.s3_key)
      images = this.state.images.map(image => {
        if (_.includes(keys, image.s3_key)) {
          image = {...image, selected: !image.selected}
        }
        return image
      })
    } else {
      images = [
        ...this.state.images.slice(0, key),
        {...this.state.images[key], selected: !this.state.images[key].selected},
        ...this.state.images.slice(key+1, this.state.images.length)
      ]
    }
    this.setState({
      images: images
    })
  },
  addImagesToCollection(collection) {
    const images = this.state.images.filter(image => image.selected)
    images.forEach(image => {
      const uri = `/api/collections/${collection}/images/${image.s3_key}`
      fetch(uri, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        credentials: 'same-origin',
        method: 'PUT'
      })
    })
  },
  removeImagesFromCollection(images, collection) {
    return images.map(image => {
      const uri = `/api/collections/${collection}/images/${image.s3_key}`
      return fetch(uri, {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        credentials: 'same-origin',
        method: 'DELETE'
      })
    })
  },
  handleUpload(file) {
    fetch('/api/signed-post', {credentials: 'same-origin'})
    .then(response => {
      response.json().then(post => {
        const formData = new FormData()
        const key = post.fields.key.split('/')[0] + '/' + file.name
        Object.keys(post.fields).forEach(field => {
          formData.set(field, post.fields[field])
        })
        formData.set('Content-Type', file.type)
        formData.set('file', file)
        const xhr = new XMLHttpRequest()
        this.setState(previousState => {
          const upload = {
            filename: file.name,
            message: 'Waiting to upload.',
            state: 'wait',
            loaded: 0,
            total: file.size
          }
          return {...previousState, uploads: {...previousState.uploads, [key]: upload}}
        })
        xhr.upload.addEventListener('progress', event => {
          if (event.lengthComputable) {
            this.setState(previousState => {
              const upload = {
                ...previousState.uploads[key],
                message: 'Uploading.',
                state: 'upload',
                loaded: event.loaded,
                total: event.total
              }
              return {...previousState, uploads: {...previousState.uploads, [key]: upload}}
            })
          }
        })
        xhr.addEventListener('load', event => {
          this.setState(previousState => {
            const upload = {
              ...previousState.uploads[key],
              filename: (<a href={`${post.url}${key}`} target='_blank'>{file.name}</a>),
              message: 'Creating thumbnails.',
              state: 'thumb',
              loaded: file.size,
              total: file.size
            }
            return {...previousState, uploads: {...previousState.uploads, [key]: upload}}
          })
          this.createImage({'s3_key': key})
        })
        xhr.addEventListener('error', event => {
          this.setState(previousState => {
            const upload = {
              ...previousState.uploads[key],
              message: 'Error uploading file.',
              state: 'error',
              loaded: 0,
              total: file.size
            }
            return {...previousState, uploads: {...previousState.uploads, [key]: upload}}
          })
        })
        xhr.addEventListener('abort', event => {
          this.setState(previousState => {
            const upload = {
              ...previousState.uploads[key],
              message: 'Upload aborted.',
              state: 'abort',
              loaded: 0,
              total: file.size
            }
            return {...previousState, uploads: {...previousState.uploads, [key]: upload}}
          })
        })
        xhr.open('POST', post.url, true)
        xhr.send(formData)
      })
    })
  },
  setUser(user) {
    this.setState({
      user: user
    })
  },
  getLoggedInUser() {
    fetch('/api/session', {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      credentials: 'same-origin'
    })
    .then(response => {
      if (response.status === 200) {
        response.json().then(session => {
          if (session.loggedIn) {
            this.setState({
              user: session.user
            })
            this.updateApiKeys()
            this.updateCollections()
          }
        })
      }
    })
  },
  updateApiKeys() {
    if (!this.state.user) {
      this.setState({
        apiKeys: []
      })
      return
    }
    fetch('/api/api-keys', {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      credentials: 'same-origin'
    })
    .then(response => {
      if (response.status === 200) {
        response.json().then(apiKeys => {
          this.setState({
            apiKeys: apiKeys
          })
        })
      }
    })
  },
  updateCollections() {
    if (!this.state.user) {
      this.setState({
        collections: []
      })
      return
    }
    fetch('/api/collections', {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      credentials: 'same-origin'
    })
    .then(response => {
      if (response.status === 200) {
        response.json().then(collections => {
          this.setState({
            collections: collections
          })
        })
      }
    })
  },
  updateImages(uri) {
    if (!this.state.user) {
      this.setState({
        images: []
      })
      return
    }
    uri = uri || '/api/images'
    fetch(uri, {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      credentials: 'same-origin'
    })
    .then(response => {
      if (response.status === 200) {
        response.json().then(images => {
          this.setState({
            images: images.map(image => {
              let primary_color_brightness
              if (image.colors) {
                primary_color_brightness = _.chunk(
                  image.colors[0].split('').slice(1),
                  2
                )
                .map(color => color.join(''))
                .map(color => parseInt(color, 16))
                .reduce((p, c) => p + c)
              }
              let bright
              if (image.colors && primary_color_brightness > 384) {
                bright = true
              } else {
                bright = false
              }
              return {
                ...image,
                selected: false,
                bright: bright
              }
            })
          })
        })
      }
    })
  },
  componentDidMount() {
    this.getLoggedInUser()
  },
  getInitialState() {
    return {
      user: null,
      apiKeys: [],
      collections: [],
      images: [],
      uploads: {},
      currentCollection: null,
      currentImage: null
    }
  },
  render() {
    return (
      <div className='app-container'>
        <Nav user={this.state.user} />
        <div className='app-content'>
          {
            React.cloneElement(
              this.props.children,
              {
                setUser: this.setUser,
                handleUpload: this.handleUpload,
                toggleImageSelect: this.toggleImageSelect,
                addImagesToCollection: this.addImagesToCollection,
                removeImagesFromCollection: this.removeImagesFromCollection,
                updateApiKeys: this.updateApiKeys,
                updateCollections: this.updateCollections,
                updateImages: this.updateImages,
                user: this.state.user,
                apiKeys: this.state.apiKeys,
                collections: this.state.collections,
                images: this.state.images,
                uploads: this.state.uploads
              }
            )
          }
        </div>
      </div>
    )
  }
})
