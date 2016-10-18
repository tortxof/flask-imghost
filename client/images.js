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
      style={{backgroundImage: `url(https://s3.amazonaws.com/${image.s3_bucket}/${image.s3_key})`}}
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
      <Image image={image} />
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
