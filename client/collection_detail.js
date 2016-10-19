import React from 'react'

import {Image} from './images'

export default React.createClass({
  getInitialState() {
    return {collection: {images: []}}
  },
  componentDidMount() {
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
          this.setState({
            collection: collection
          })
        })
      }
    })
  },
  render() {
    const images = this.state.collection.images.map(image => (
      <Image
        key={image.s3_key}
        image={image}
      />
    ))
    return (
      <div className='collection-detail'>
        <div>Collection: {this.props.params.name}</div>
        <div className='images'>
          {images}
        </div>
      </div>
    )
  }
})
