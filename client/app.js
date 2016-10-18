import React from 'react'

import Nav from './nav'

export default React.createClass({
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
        xhr.upload.addEventListener('progress', event => {
          if (event.lengthComputable) {
            this.setState(previousState => {
              const uploads = Object.assign({}, previousState.uploads)
              uploads[key] = {
                filename: file.name,
                message: 'Uploading...',
                loaded: event.loaded,
                total: event.total
              }
              return {uploads: uploads}
            })
          }
        })
        xhr.addEventListener('load', event => {
          this.setState(previousState => {
            const uploads = Object.assign({}, previousState.uploads)
            uploads[key] = {
              filename: (<a href={`${post.url}${key}`} target='_blank'>{file.name}</a>),
              message: 'Upload complete.',
              loaded: file.size,
              total: file.size
            }
            return {uploads: uploads}
          })
        })
        xhr.addEventListener('error', event => {
          this.setState(previousState => {
            const uploads = Object.assign({}, previousState.uploads)
            uploads[key] = {
              filename: file.name,
              message: 'Error uploading file.',
              loaded: 0,
              total: file.size
            }
            return {uploads: uploads}
          })
        })
        xhr.addEventListener('abort', event => {
          this.setState(previousState => {
            const uploads = Object.assign({}, previousState.uploads)
            uploads[key] = {
              filename: file.name,
              message: 'Upload aborted.',
              loaded: 0,
              total: file.size
            }
            return {uploads: uploads}
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
                updateApiKeys: this.updateApiKeys,
                updateCollections: this.updateCollections,
                apiKeys: this.state.apiKeys,
                collections: this.state.collections,
                uploads: this.state.uploads
              }
            )
          }
        </div>
      </div>
    )
  }
})
