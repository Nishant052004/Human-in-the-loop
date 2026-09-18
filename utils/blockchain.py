import hashlib
import json
import time
import sqlite3
from database.db import conn, cursor

def calculate_hash(block_index, timestamp, data_json, prev_hash):
    """Calculate SHA-256 hash of a block."""
    block_string = f"{block_index}{timestamp}{data_json}{prev_hash}"
    return hashlib.sha256(block_string.encode('utf-8')).hexdigest()

def init_blockchain():
    """Ensure the blockchain has at least the genesis block."""
    cursor.execute("SELECT COUNT(*) FROM blockchain")
    count = cursor.fetchone()[0]
    if count == 0:
        # Create Genesis Block
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        data = json.dumps({"message": "Genesis Block - HAULT DevOps Auditor Initiated"})
        prev_hash = "0" * 64
        block_hash = calculate_hash(0, timestamp, data, prev_hash)
        
        cursor.execute("""
        INSERT INTO blockchain (block_index, timestamp, data_json, prev_hash, block_hash)
        VALUES (?, ?, ?, ?, ?)
        """, (0, timestamp, data, prev_hash, block_hash))
        conn.commit()

def add_blockchain_block(data_dict):
    """Add a new block to the blockchain ledger."""
    init_blockchain()
    
    # Get last block to fetch prev_hash and block_index
    cursor.execute("SELECT block_index, block_hash FROM blockchain ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    last_index = row[0]
    prev_hash = row[1]
    
    new_index = last_index + 1
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    data_json = json.dumps(data_dict)
    
    new_hash = calculate_hash(new_index, timestamp, data_json, prev_hash)
    
    cursor.execute("""
    INSERT INTO blockchain (block_index, timestamp, data_json, prev_hash, block_hash)
    VALUES (?, ?, ?, ?, ?)
    """, (new_index, timestamp, data_json, prev_hash, new_hash))
    conn.commit()
    return new_hash

def verify_chain_integrity():
    """Recalculates all hashes in the blockchain to verify that no records have been tampered with."""
    init_blockchain()
    cursor.execute("SELECT block_index, timestamp, data_json, prev_hash, block_hash FROM blockchain ORDER BY id ASC")
    blocks = cursor.fetchall()
    
    report = []
    is_valid = True
    
    for i in range(len(blocks)):
        index, timestamp, data_json, prev_hash, stored_hash = blocks[i]
        
        # Check prev_hash links
        if i > 0:
            _, _, _, _, expected_prev_hash = blocks[i-1]
            if prev_hash != expected_prev_hash:
                report.append(f"❌ Block {index}: Tampered Link! Previous hash link is broken.")
                is_valid = False
                continue
                
        # Check current block hash calculation
        calculated = calculate_hash(index, timestamp, data_json, prev_hash)
        if calculated != stored_hash:
            report.append(f"❌ Block {index}: Content Tampered! Stored hash doesn't match content.")
            is_valid = False
        else:
            report.append(f"✅ Block {index} Integrity Verified.")
            
    return is_valid, report
