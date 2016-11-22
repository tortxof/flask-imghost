import React from 'react'
import _ from 'lodash'

import {Image} from './images'

export default React.createClass({
  componentDidMount() {
    this.props.setImagesUri(
      `/api/collections/${this.props.params.name}/images`,
      () => {
        const tryImages = () => {
          if (!this.props.user) {
            setTimeout(tryImages, 1000)
          } else {
            this.props.updateImages()
          }
        }
        tryImages()
      }
    )
  },
  handleRemove() {
    const images = this.props.images.filter(image => image.selected)
    const collection = this.props.params.name
    Promise.all(this.props.removeImagesFromCollection(images, collection))
    .then(responses => {this.props.updateImages()})
  },
  render() {
    const images = this.props.images.map((image, i) => (
      <Image
        key={image.s3_key}
        index={i}
        image={image}
        handleClick={this.props.toggleImageSelect}
        updateImage={_.debounce(this.props.updateImage, 3000)}
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
