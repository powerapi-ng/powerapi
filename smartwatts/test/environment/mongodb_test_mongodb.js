// Javascript script for create test environment with MongoDB
// !! You don't have to run this script manually, it's done
// !! in "mongodb.sh" bash script

// Create "test_mongodb" database
conn = new Mongo();
db = conn.getDB("test_mongodb");

// Recreate empty collection "test_mongodb1"
// and "test_mongodb2"
db.test_mongodb1.drop()
db.test_mongodb2.drop()
db.createCollection("test_mongodb1");
db.createCollection("test_mongodb2", {capped: true, size: 256*40});

// Feed the collection "test_mongodb1"
// with HWPCReport
for (var i = 0 ; i < 10 ; i++)
{
 db.test_mongodb1.insert({
  _id: i,
  timestamp: Date.now(),
  sensor: 'sensor_test',
  target: 'system',
  groups: {
   megagroup: {
    0 : {
     0 : {
      'event1': 100,
      'event2': 200
     }
    }
   }
  }
 })
}

// Feed the collection "test_mongodb2"
// with HWPCReport
for (var i = 0 ; i < 10 ; i++)
{
 db.test_mongodb2.insert({
  _id: i,
  timestamp: Date.now(),
  sensor: 'sensor_test',
  target: 'system',
  groups: {
   megagroup: {
    0 : {
     0 : {
      'event1': 100,
      'event2': 200
     }
    }
   }
  }
 })
}
