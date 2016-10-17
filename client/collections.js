import React from 'react'

const Collection = ({
  collection
}) => (
  <div className='collection'>
    <div>{collection.name}</div>
  </div>
)

export default React.createClass({
  componentDidMount() {
    this.props.updateCollections()
  },
  render() {
    return (
      <div>
        <div>Collections</div>
        {
          this.props.collections.map(
            collection => (
              <Collection
                collection={collection}
                key={collection.name}
              />
            )
          )
        }
      </div>
    )
  }
})
