import React from 'react'
import _ from 'lodash'

export const Image = React.createClass({
  getInitialState() {
    return {
      title: this.props.image.title,
      description: this.props.image.description
    }
  },
  handleTitleChange(e) {
    this.setState({
      title: e.target.value
    })
    this.props.updateImage({
      uri: this.props.image.uri,
      title: e.target.value,
      description: this.state.description
    })
  },
  handleDescriptionChange(e) {
    this.setState({
      description: e.target.value
    })
    this.props.updateImage({
      uri: this.props.image.uri,
      title: this.state.title,
      description: e.target.value
    })
  },
  render() {
    return (
      <div
        className={
          'image' +
          (this.props.image.selected ? ' selected' : '') +
          (this.props.image.bright ? ' bright' : '')
        }
        style={this.props.image.colors ? {backgroundColor: this.props.image.colors[0]} : {}}
      >
        <div className='link'>
          <a
            target='_blank'
            href={this.props.image.url}
          >
            {this.props.image.s3_key.split('/').slice(1).join('')}
          </a>
        </div>
        {this.props.image.thumbs ?
          <div
            className='thumb'
            style={{
              backgroundImage: `url(${this.props.image.thumbs['256'].url})`
            }}
          >
          </div> :
          null
        }
        <input className='title' value={this.state.title} onChange={this.handleTitleChange} />
        <input className='description' value={this.state.description} onChange={this.handleDescriptionChange} />
        <div className='colors'>
          {this.props.image.colors ? this.props.image.colors.slice(1).map((color, i) => (
            <div key={i} className='color' style={{backgroundColor: color}}></div>
          )) : null}
        </div>
        <button data-key={this.props.index} onClick={this.props.handleClick}>Select</button>
      </div>
    )
  }
})

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
    this.props.setImagesNeedUpdate()
    const tryImages = () => {
      if (!this.props.user) {
        console.log('waiting')
        setTimeout(tryImages, 1000)
      } else {
        this.props.updateImages()
      }
    }
    tryImages()
  },
  render() {
    const images = this.props.images.map((image, i) => (
      <Image
        key={i}
        index={i}
        image={image}
        handleClick={this.props.toggleImageSelect}
        updateImage={_.debounce(this.props.updateImage, 3000)}
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
          {this.props.imagesNeedUpdate ? null : images}
        </div>
      </div>
    )
  }
})
