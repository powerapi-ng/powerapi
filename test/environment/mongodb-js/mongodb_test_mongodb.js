// Javascript script for create test environment with MongoDB
// !! You don't have to run this script manually, it's done
// !! in "mongodb.sh" bash script

load('./mongodb-js/report_generator.js');

// Create "test_mongodb" database
conn = new Mongo();
db = conn.getDB("test_mongodb");

// Recreate empty collection "test_mongodb1"
// and "test_mongodb2"
db.test_mongodb1.drop()
db.test_mongodb2.drop()
db.test_mongodb3.drop()
db.createCollection("test_mongodb1");
db.createCollection("test_mongodb2", {capped: true, size: 256*40});
db.createCollection("test_mongodb3");

// Feed the collection "test_mongodb1"
// with HWPCReport
for (var i = 0 ; i < 10 ; i++)
{
 db.test_mongodb1.insert(generate_hwpc(i, 'sensor_test', 'system'));
}

// Feed the collection "test_mongodb2"
// with HWPCReport
for (var i = 0 ; i < 10 ; i++)
{
 db.test_mongodb2.insert(generate_hwpc(i, 'sensor_test', 'system'));
}

// Feed the collection "test_mongodb3"
// with random data
for (var i = 0 ; i < 2 ; i++)
{
 db.test_mongodb3.insert({'key': 'value'});
}
