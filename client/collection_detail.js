import React from 'react'

import {Image} from './images'

export default React.createClass({
  getInitialState() {
    return {collection: {images: []}}
  },
  componentDidMount() {
    this.props.updateImages(`/api/collections/${this.props.params.name}/images`)
    this.setState({collection: {name: this.props.params.name}})
  },
  handleRemove() {
    const images = this.props.images.filter(image => image.selected)
    const collection = this.state.collection.name
    Promise.all(this.props.removeImagesFromCollection(images, collection))
    .then(responses => {this.props.updateImages(`/api/collections/${this.props.params.name}/images`)})
  },
  render() {
    const images = this.props.images.map((image, i) => (
      <Image
        key={i}
        index={i}
        image={image}
        handleClick={this.props.toggleImageSelect}
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
