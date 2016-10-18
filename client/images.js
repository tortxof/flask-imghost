import React from 'react'

const Image = ({
  image
}) => (
  <div className='image'>
    <div className='link'>
      <a
        target='_blank'
        href={`https://s3.amazonaws.com/${image.s3_bucket}/${image.s3_key}`}
      >
        {image.s3_key}
      </a>
    </div>
    <div
      className='thumb'
      style={{backgroundImage: `url(https://s3.amazonaws.com/${image.s3_bucket}/${image.s3_key.split('/')[0]}/t256/${image.s3_key.split('/').slice(1)})`}}
    >
    </div>
  </div>
)

export default React.createClass({
  componentDidMount() {
    this.props.updateImages()
  },
  render() {
    const images = this.props.images.map(image => (
      <Image key={image.s3_key} image={image} />
    ))
    return (
      <div>
        <div>Images</div>
        <div className='images'>
          {images}
        </div>
      </div>
    )
  }
})
