fos = require('./store.js').fog05

rt = new fos.Runtime('ws://localhost:9669')
rt.onconnect = () ->
  store = new fos.Store(rt, 101, 'fos://root/', 'fos://root/kydos', 1024)
  store.put('fos://root/kydos/one', 1)
  store.put('fos://root/kydos/two', 2)
  store.get('fos://root/kydos/two',
    (k, v) -> console.log("Received <#{k}, #{v.show()}")
  )
  store.get('fos://root/kydos/one',
    (k, v) -> console.log("Received <#{k}, #{v.show()}"))

  store.getAll('fos://root/kydos/*',
    (k, vs) -> console.log("Received <#{k}, #{vs}"))

rt.connect()


