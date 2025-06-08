# How to run MCP server

## Step 1 - Installation of database
(if you have your database - update your code for connection, and skip this part)
We need to create local database
`docker run --name my-postgres -e POSTGRES_PASSWORD=mypassword -p 5432:5432 -d postgres`
This command will pull docker image and run it

`docker exec -it my-postgres psql -U postgres`
This command will open terminal to your docker container 

### 1.2 Create tables
When you're inside your database (see command in the top) - you can create tables and fill it with data - use this commands

`-- migration.sql
-- Drop tables if they already exist to ensure clean migration`
DROP TABLE IF EXISTS transactions;\
DROP TABLE IF EXISTS articles;\
DROP TABLE IF EXISTS customers;

`-- Create the customers table`\
CREATE TABLE customers (\
    customer_id TEXT PRIMARY KEY,\
    first_name TEXT,\
    active BOOLEAN,\
    club_member_status TEXT,\
    fashion_news_frequency TEXT,\
    age INTEGER,\
    postal_code TEXT\
);

`-- Create the articles table`\
CREATE TABLE articles (\
    article_id TEXT PRIMARY KEY,\
    product_code TEXT,\
    prod_name TEXT,\
    product_type_no INTEGER,\
    product_type_name TEXT,\
    product_group_name TEXT,\
    graphical_appearance_no INTEGER,\
    graphical_appearance_name TEXT,\
    colour_group_code TEXT,\
    colour_group_name TEXT,\
    perceived_colour_value_id INTEGER,\
    perceived_colour_value_name TEXT,\
    perceived_colour_master_id INTEGER,\
    perceived_colour_master_name TEXT,\
    department_no INTEGER,\
    department_name TEXT,\
    index_code TEXT,\
    index_name TEXT,\
    index_group_no INTEGER,\
    index_group_name TEXT,\
    section_no INTEGER,\
    section_name TEXT,\
    garment_group_no INTEGER,\
    garment_group_name TEXT, \
    detail_desc TEXT \
);

`-- Create the transactions table`\
CREATE TABLE transactions (\
    transaction_date DATE,\
    customer_id TEXT REFERENCES customers(customer_id),\
    article_id TEXT REFERENCES articles(article_id),\
    price NUMERIC(10, 6),\
    sales_channel_id INTEGER\
);

`-- Optional: Indexes to improve performance`\
CREATE INDEX idx_transactions_customer_id ON transactions(customer_id);\
CREATE INDEX idx_transactions_article_id ON transactions(article_id);\
CREATE INDEX idx_transactions_date ON transactions(transaction_date);\
`

### 1.3 Save data to DB 
`-- sample_data.sql`\
`-- Insert sample customers`\

INSERT INTO customers (customer_id, first_name, active, club_member_status, fashion_news_frequency, age, postal_code) VALUES\
('c001', 'Emma', true, 'ACTIVE', 'Regularly', 28, '10001'),\
('c002', 'James', true, 'LEFT CLUB', 'Monthly', 34, '10002'),\
('c003', 'Sofia', false, 'ACTIVE', 'None', 22, '10003'),\
('c004', 'Lucas', true, 'PRE_CREATE', 'Regularly', 45, '10004'),\
('c005', 'Aria', true, 'ACTIVE', 'Regularly', 31, '10005'),\
('c006', 'Oliver', true, 'ACTIVE', 'Monthly', 38, '10006'),\
('c007', 'Isabella', false, 'LEFT CLUB', 'None', 26, '10007'),\
('c008', 'Noah', true, 'ACTIVE', 'Regularly', 29, '10008'),\
('c009', 'Mia', true, 'PRE_CREATE', 'Monthly', 33, '10009'),\
('c010', 'Liam', true, 'ACTIVE', 'Regularly', 41, '10010');

`-- Insert sample articles`\

INSERT INTO articles (article_id, product_code, prod_name, product_type_no, product_type_name, product_group_name, graphical_appearance_no, graphical_appearance_name, colour_group_code, colour_group_name, perceived_colour_value_id, perceived_colour_value_name, perceived_colour_master_id, perceived_colour_master_name, department_no, department_name, index_code, index_name, index_group_no, index_group_name, section_no, section_name, garment_group_no, garment_group_name, detail_desc) VALUES
('a001', 'PC001', 'Slim Fit Jeans', 1, 'Trousers', 'Garment Lower body', 1, 'Solid', 'Blue', 'Blue', 1, 'Dark', 1, 'Blue', 1, 'Menswear', 'A', 'Ladieswear', 1, 'Garments', 1, 'Womens Everyday Basics', 1, 'Jeans', 'Classic denim jeans'),
('a002', 'PC002', 'Cotton T-Shirt', 2, 'T-shirt', 'Garment Upper body', 2, 'Solid', 'White', 'White', 2, 'Light', 2, 'White', 2, 'Womenwear', 'B', 'Basics', 2, 'Garments', 2, 'Womens Everyday Collection', 2, 'Jersey Basic', 'Basic cotton t-shirt'),
('a003', 'PC003', 'Leather Jacket', 3, 'Jacket', 'Garment Upper body', 3, 'Solid', 'Black', 'Black', 3, 'Dark', 3, 'Black', 3, 'Menswear', 'C', 'Outerwear', 3, 'Garments', 3, 'Mens Trend', 3, 'Outdoor', 'Premium leather jacket'),
('a004', 'PC004', 'Summer Dress', 4, 'Dress', 'Garment Full body', 4, 'Print', 'Red', 'Red', 4, 'Medium', 4, 'Red', 4, 'Womenwear', 'D', 'Dresses', 4, 'Garments', 4, 'Womens Trend', 4, 'Dresses', 'Floral summer dress'),
('a005', 'PC005', 'Running Shoes', 5, 'Shoes', 'Shoes', 5, 'Solid', 'Grey', 'Grey', 5, 'Medium', 5, 'Grey', 5, 'Sport', 'E', 'Footwear', 5, 'Shoes', 5, 'Sport', 5, 'Shoes', 'Athletic running shoes'),
('a006', 'PC006', 'Wool Sweater', 6, 'Sweater', 'Garment Upper body', 6, 'Solid', 'Navy', 'Blue', 6, 'Dark', 1, 'Blue', 6, 'Menswear', 'F', 'Knitwear', 6, 'Garments', 6, 'Mens Basics', 6, 'Knitwear', 'Warm wool sweater'),
('a007', 'PC007', 'Silk Blouse', 7, 'Blouse', 'Garment Upper body', 7, 'Solid', 'Pink', 'Pink', 7, 'Light', 6, 'Pink', 7, 'Womenwear', 'G', 'Blouses', 7, 'Garments', 7, 'Womens Contemporary', 7, 'Blouses & Shirts', 'Elegant silk blouse'),
('a008', 'PC008', 'Denim Shorts', 8, 'Shorts', 'Garment Lower body', 8, 'Solid', 'Blue', 'Blue', 8, 'Medium', 1, 'Blue', 8, 'Womenwear', 'H', 'Shorts', 8, 'Garments', 8, 'Womens Casual', 8, 'Shorts', 'Casual denim shorts'),
('a009', 'PC009', 'Formal Shirt', 9, 'Shirt', 'Garment Upper body', 9, 'Solid', 'White', 'White', 9, 'Light', 2, 'White', 9, 'Menswear', 'I', 'Shirts', 9, 'Garments', 9, 'Mens Formal', 9, 'Shirts', 'Business formal shirt'),
('a010', 'PC010', 'Knit Cardigan', 10, 'Cardigan', 'Garment Upper body', 10, 'Solid', 'Beige', 'Beige', 10, 'Light', 7, 'Beige', 10, 'Womenwear', 'J', 'Cardigans', 10, 'Garments', 10, 'Womens Knitwear', 10, 'Knitwear', 'Cozy knit cardigan');

`-- Insert sample transactions`\
INSERT INTO transactions (transaction_date, customer_id, article_id, price, sales_channel_id) VALUES
('2024-01-15', 'c001', 'a001', 79.99, 1),
('2024-01-15', 'c001', 'a002', 19.99, 1),
('2024-01-16', 'c002', 'a003', 199.99, 2),
('2024-01-17', 'c003', 'a004', 49.99, 1),
('2024-01-17', 'c004', 'a005', 89.99, 1),
('2024-01-18', 'c005', 'a006', 59.99, 1),
('2024-01-18', 'c005', 'a007', 79.99, 1),
('2024-01-19', 'c006', 'a008', 39.99, 2),
('2024-01-20', 'c007', 'a009', 69.99, 1),
('2024-01-20', 'c008', 'a010', 89.99, 1),
('2024-01-21', 'c009', 'a001', 79.99, 2),
('2024-01-22', 'c010', 'a002', 19.99, 1),
('2024-01-22', 'c001', 'a005', 89.99, 2),
('2024-01-23', 'c002', 'a007', 79.99, 1),
('2024-01-24', 'c003', 'a009', 69.99, 1),
('2024-01-25', 'c004', 'a010', 89.99, 2),
('2024-01-26', 'c005', 'a003', 199.99, 1),
('2024-01-27', 'c006', 'a004', 49.99, 1),
('2024-01-28', 'c007', 'a001', 79.99, 2),
('2024-01-29', 'c008', 'a008', 39.99, 1);

## Step 2 - settings for Claude Desktop 
Download Claude Desktop - https://claude.ai/download

Run it and edit settings (Settings -> Developer -> Edit config). Open file claude_desktop_config.json and insert these settings
`{
  "mcpServers": {
    "ecommerce-server": {
      "command": "python3",
      "args": ["/Users/bakytn/Desktop/ecole42/hf_ecom_analyst/mcp-server/mcp_server_only.py"],
      "env": {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "postgres",
        "DB_USER": "postgres",
        "DB_PASSWORD": "mypassword"
      }
    }
  }
}`
Don't forget to reboot Claude desktop 

## Step 3 - Create env file in mcp-server folder
`DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=mypassword
GRADIO_PORT=7860`


## Step 3 - Run code 
1. Install dependencies in requirements.txt (up to you, local virtual environment or global) 
2. In Terminal 1 run MCP server itself with "python3 mcp_server_only.py" (folder mcp-server). This command will run server and you can start use Clause Desktop
3. If you want gradio interface - in Terminal 2 run "python3 gradio_dashboard.py".

In Claude Desktop - just enter your prompts 

For Gradio interface - go to http://localhost:7860/

Links to screenshots 
[https://ibb.co/Psbgx6NG](url)
[https://ibb.co/Fb60B7qD](url)
[https://ibb.co/RkfvLFGj](url)
[https://ibb.co/qMVQzcHt](url)

![pic1](https://i.ibb.co/Q3Lbsg7D/Screenshot-2025-06-05-at-01-23-23.png)



for sacha test on the anova:
{'type_1': [52.483570765056164,
  49.308678494144075,
  53.23844269050346,
  57.61514928204013,
  48.82923312638332,
  48.8293152152541,
  57.896064077536955,
  53.837173645764544,
  47.65262807032524,
  52.712800217929825,
  47.68291153593769,
  47.671351232148716,
  51.20981135783017,
  40.43359877671101,
  41.375410837434835,
  47.188562353795135,
  44.93584439832788,
  51.57123666297637,
  45.45987962239394,
  42.93848149332354,
  57.32824384460777,
  48.87111849756732,
  50.337641023439616,
  42.87625906893272,
  47.27808637737409,
  50.554612948549334,
  44.24503211288849,
  51.87849009172836,
  46.99680655040598,
  48.54153125103362],
 'type_2': [51.991466938853016,
  64.26139092254469,
  54.93251387631033,
  49.7114453552205,
  59.11272456051594,
  48.89578175014489,
  56.04431797502378,
  45.201649380601125,
  48.359069755507846,
  55.984306179345616,
  58.69233289997705,
  55.85684140594985,
  54.4217585880588,
  53.494481522053555,
  47.60739004816286,
  51.40077895802646,
  52.696806145201066,
  60.285611131094576,
  56.718091447842305,
  46.18479922318633,
  56.620419846973974,
  53.07458859791842,
  51.61538999847021,
  58.058381444204336,
  60.154997612479754,
  59.65640059558099,
  50.80391238388681,
  53.45393812074393,
  56.65631715701782,
  59.877725635611796],
 'type_3': [57.60412881077355,
  59.07170511668092,
  54.468325129969855,
  54.01896687959665,
  64.06262911197099,
  66.78120014285412,
  59.63994939209833,
  65.01766448946012,
  61.808180125238174,
  56.774401226974376,
  61.80697802754207,
  67.69018283232984,
  59.82086980445024,
  67.82321827907003,
  46.901274479551276,
  64.10951252187611,
  60.435235341190854,
  58.50496324767066,
  60.458803882677515,
  50.06215542699554,
  58.90164056081244,
  61.78556285755873,
  67.38947022370758,
  57.40864890863176,
  55.95753198553406,
  57.491214782077314,
  64.57701058851038,
  61.64375554829842,
  57.351198981164806,
  62.56633716556678],
 'type_4': [65.4853877467402,
  69.84322495266444,
  61.48973453061324,
  63.36168926701116,
  63.03945923433921,
  57.68242525933941,
  66.48060138532288,
  66.30527636089944,
  65.02556728321231,
  63.82706433312426,
  57.923146289747926,
  62.89677338617321,
  63.286427417366156,
  60.9886136538919,
  64.19357144166996,
  67.02025428407269,
  74.43092950605265,
  65.8728890641592,
  66.28775195361382,
  64.62777042116916,
  55.40614392350479,
  64.86743062275391,
  65.30115104970513,
  77.31621056242643,
  64.03819517609439,
  66.50773671166806,
  64.82644115147379,
  59.15660981190234,
  70.7141140725751,
  68.75966516343387],
 'type_5': [73.95515973521523,
  65.4530627260263,
  77.0139715546805,
  62.990744686038596,
  72.93428546900135,
  80.95227812904989,
  65.04731837434656,
  67.16851135198614,
  70.4982568254382,
  67.48262172941901,
  62.24668284466934,
  70.34281487403014,
  64.68848143136948,
  72.36796215317591,
  65.40287882883098,
  77.7496720250877,
  66.08373353831881,
  68.38969241897162,
  74.06758608684835,
  63.84567841783022,
  71.13729967302065,
  76.53571377141213,
  61.96258382719386,
  70.92316929266153,
  71.29941397124212,
  73.90911435888655,
  63.81524644560959,
  63.39771693457862,
  72.60970782808448,
  71.48492336616593]}