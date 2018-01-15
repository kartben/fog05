fos = require('./store.js').fog05

rt = new fos.Runtime('ws://localhost:9669')
rt.onconnect = () ->
  store = new fos.Store(rt, 101, 'fos://root/', 'fos://root/kydos', 1024)
  store.put('fos://root/kydos/one', 1)
  store.put('fos://root/kydos/two', 2)
  store.get('fos://root/kydos/two',
    (k, v) -> console.log("get #{k} -> #{v.show()}")
  )
  store.get('fos://root/kydos/one',
    (k, v) -> console.log("get #{k} ->  #{v.show()}"))

  store.getAll('fos://root/kydos/*',
    (k, vs) -> console.log("aget #{k} -> #{JSON.stringify(vs)}"))

  #store.keys( (ks) -> console.log("keys -> #{JSON.stringify(ks)}"))

  store.get('afos://<sys-id>/84610ec8a5424b67a776d5d79e904ff7/plugins',
    (k, v) -> console.log("get #{k} -> #{v.show()}")
  )

rt.connect()


