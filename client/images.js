import React from 'react'

const Image = ({
  image,
  handleClick
}) => (
  <div className={'image' + (image.selected ? ' selected' : '')}>
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
    <button data-key={image.s3_key} onClick={handleClick}>Select</button>
  </div>
)

const RadioInput = ({
  collectionName,
  selectedCollection,
  handleChange
}) => (
  <div>
    <input
      className='collection-select'
      type='radio'
      name='collection'
      value={collectionName}
      checked={selectedCollection === collectionName}
      onChange={handleChange}
    />
    {collectionName}
  </div>
)

const CollectionSelect = React.createClass({
  handleSubmit(e) {
    e.preventDefault()
    console.log(e.target)
  },
  handleChange(e) {
    this.setState({
      collection: e.target.value
    })
  },
  getInitialState() {
    return {collection: null}
  },
  render() {
    return (
      <div>
        {this.props.collections.map(collection => (
          <RadioInput
            key={collection.name}
            collectionName={collection.name}
            selectedCollection={this.state.collection}
            handleChange={this.handleChange}
          />
        ))}
        <button>Add to collection</button>
      </div>
    )
  }
})

export default React.createClass({
  componentDidMount() {
    this.props.updateImages()
    this.props.updateCollections()
  },
  render() {
    const images = this.props.images.map(image => (
      <Image
        key={image.s3_key}
        image={image}
        handleClick={this.props.toggleImageSelect}
      />
    ))
    return (
      <div>
        <div>Images</div>
        <CollectionSelect
          collections={this.props.collections}
          images={this.props.images}
        />
        <div className='images'>
          {images}
        </div>
      </div>
    )
  }
})
