fos = require('./store-node.coffee').fog05

rt = new fos.Runtime('ws://localhost:9669/a1b2c3d4')
rt.onconnect = () ->
  store = new fos.Store(rt, 101, '/', '/kydos', 1024)
  store.put('/a/one', 1)
  store.put('/a/two', 2)
  store.get('/a/two',
    (k, v) -> console.log("get #{k} -> #{v.show()}")
  )
  store.get('/a/one',
    (k, v) -> console.log("get #{k} ->  #{v.show()}"))

  store.getAll('/a/*',
    (k, vs) -> console.log("aget #{k} -> #{JSON.stringify(vs)}"))

  store.keys( (ks) -> console.log("keys -> #{JSON.stringify(ks)}"))

  store.observe('/a/*', (d) -> console.log("observer  -> #{JSON.stringify(d)}"))

rt.connect()

#
# s.get('/a/one', (k, v) -> console.log("get #{k} ->  #{v.show()}"))