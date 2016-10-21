import React from 'react'

import {Image} from './images'

export default React.createClass({
  getInitialState() {
    return {collection: {images: []}}
  },
  componentDidMount() {
    this.updateImages()
  },
  updateImages() {
    if (!this.props.user) {
      this.setState(this.getInitialState())
      return
    }
    const uri = `/api/collections/${this.props.params.name}`
    fetch(uri, {
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      credentials: 'same-origin'
    })
    .then(response => {
      if (response.status === 200) {
        response.json().then(collection => {
          collection.images = collection.images.map(image => {
            return Object.assign({}, image, {selected: false})
          })
          this.setState({
            collection: collection
          })
        })
      }
    })
  },
  toggleImageSelect(e) {
    const key = e.target.dataset.key
    const images = this.state.collection.images.map(image => {
      if (image.s3_key === key) {
        image.selected = !image.selected
      }
      return image
    })
    this.setState({
      collection: Object.assign({}, this.state.collection, {images: images})
    })
  },
  handleRemove() {
    const images = this.state.collection.images.filter(image => image.selected)
    const collection = this.state.collection.name
    Promise.all(this.props.removeImagesFromCollection(images, collection))
    .then(responses => {this.updateImages()})
  },
  render() {
    const images = this.state.collection.images.map(image => (
      <Image
        key={image.s3_key}
        image={image}
        handleClick={this.toggleImageSelect}
      />
    ))
    return (
      <div className='collection-detail'>
        <div>Collection: {this.props.params.name}</div>
        <button onClick={this.handleRemove}>Remove from collection</button>
        <div className='images'>
          {images}
        </div>
      </div>
    )
  }
})
