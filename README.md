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
DROP TABLE IF EXISTS customers;\

`-- Create the customers table`
CREATE TABLE customers (\
    customer_id TEXT PRIMARY KEY,\
    first_name TEXT,\
    active BOOLEAN,\
    club_member_status TEXT,\
    fashion_news_frequency TEXT,\
    age INTEGER,\
    postal_code TEXT\
);\

-- Create the articles table
CREATE TABLE articles (
    article_id TEXT PRIMARY KEY,
    product_code TEXT,
    prod_name TEXT,
    product_type_no INTEGER,
    product_type_name TEXT,
    product_group_name TEXT,
    graphical_appearance_no INTEGER,
    graphical_appearance_name TEXT,
    colour_group_code TEXT,
    colour_group_name TEXT,
    perceived_colour_value_id INTEGER,
    perceived_colour_value_name TEXT,
    perceived_colour_master_id INTEGER,
    perceived_colour_master_name TEXT,
    department_no INTEGER,
    department_name TEXT,
    index_code TEXT,
    index_name TEXT,
    index_group_no INTEGER,
    index_group_name TEXT,
    section_no INTEGER,
    section_name TEXT,
    garment_group_no INTEGER,
    garment_group_name TEXT,
    detail_desc TEXT
);

-- Create the transactions table
CREATE TABLE transactions (
    transaction_date DATE,
    customer_id TEXT REFERENCES customers(customer_id),
    article_id TEXT REFERENCES articles(article_id),
    price NUMERIC(10, 6),
    sales_channel_id INTEGER
);

-- Optional: Indexes to improve performance
CREATE INDEX idx_transactions_customer_id ON transactions(customer_id);
CREATE INDEX idx_transactions_article_id ON transactions(article_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
`

### 1.3 Save data to DB 
`-- sample_data.sql`
`-- Insert sample customers`

INSERT INTO customers (customer_id, first_name, active, club_member_status, fashion_news_frequency, age, postal_code) VALUES
('c001', 'Emma', true, 'ACTIVE', 'Regularly', 28, '10001'),
('c002', 'James', true, 'LEFT CLUB', 'Monthly', 34, '10002'),
('c003', 'Sofia', false, 'ACTIVE', 'None', 22, '10003'),
('c004', 'Lucas', true, 'PRE_CREATE', 'Regularly', 45, '10004'),
('c005', 'Aria', true, 'ACTIVE', 'Regularly', 31, '10005'),
('c006', 'Oliver', true, 'ACTIVE', 'Monthly', 38, '10006'),
('c007', 'Isabella', false, 'LEFT CLUB', 'None', 26, '10007'),
('c008', 'Noah', true, 'ACTIVE', 'Regularly', 29, '10008'),
('c009', 'Mia', true, 'PRE_CREATE', 'Monthly', 33, '10009'),
('c010', 'Liam', true, 'ACTIVE', 'Regularly', 41, '10010');

`-- Insert sample articles`

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

`-- Insert sample transactions`
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




