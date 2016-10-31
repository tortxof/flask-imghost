import React from 'react'
import moment from 'moment'
import _ from 'lodash'

export const Image = React.createClass({
  getInitialState() {
    return {
      title: this.props.image.title,
      description: this.props.image.description
    }
  },
  handleTitleChange(e) {
    this.setState(
      {
        title: e.target.value
      },
      () => {
        this.props.updateImage({
          uri: this.props.image.uri,
          title: this.state.title,
          description: this.state.description
        })
      }
    )
  },
  handleDescriptionChange(e) {
    this.setState(
      {
        description: e.target.value
      },
      () => {
        this.props.updateImage({
          uri: this.props.image.uri,
          title: this.state.title,
          description: this.state.description
        })
      }
    )
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
        <div className='dimensions'>
          {this.props.image.size.width} &times; {this.props.image.size.height}
        </div>
        <div className='date-created'>
          {moment.utc(this.props.image.date_created).fromNow()}
        </div>
        <label>
          Title
          <input className='title' value={this.state.title} onChange={this.handleTitleChange} />
        </label>
        <label>
          Description
          <input className='description' value={this.state.description} onChange={this.handleDescriptionChange} />
        </label>

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
    this.props.setImagesUri(
      '/api/images',
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
