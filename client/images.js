import React from 'react'

export const Image = ({
  image,
  index,
  handleClick
}) => {
  return (
    <div
      className={'image' + (image.selected ? ' selected' : '')}
      style={image.colors ? {backgroundColor: image.colors[0]} : {}}
    >
      <div className='link'>
        <a
          className={image.bright ? 'dark' : ''}
          target='_blank'
          href={image.url}
        >
          {image.s3_key.split('/').slice(1).join('')}
        </a>
      </div>
      {image.thumbs ?
        <div
          className='thumb'
          style={{
            backgroundImage: `url(${image.thumbs['256'].url})`
          }}
        >
        </div> :
        null
      }
      <div className='colors'>
        {image.colors ? image.colors.slice(1).map((color, i) => (
          <div key={i} className='color' style={{backgroundColor: color}}></div>
        )) : null}
      </div>
      <button data-key={index} onClick={handleClick}>Select</button>
    </div>
  )
}

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
        <button onClick={() => this.props.addImagesToCollection(this.state.collection)}>Add to collection</button>
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
    const images = this.props.images.map((image, i) => (
      <Image
        key={i}
        index={i}
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
          addImagesToCollection={this.props.addImagesToCollection}
        />
        <div className='images'>
          {images}
        </div>
      </div>
    )
  }
})
