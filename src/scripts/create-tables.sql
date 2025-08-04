-- Create database tables for contract analysis system

-- Table for storing contract summaries
CREATE TABLE IF NOT EXISTS contract_summaries (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_content TEXT NOT NULL,
    summary TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for storing policy comparisons
CREATE TABLE IF NOT EXISTS policy_comparisons (
    id SERIAL PRIMARY KEY,
    contract_filename VARCHAR(255) NOT NULL,
    policy_filename VARCHAR(255) NOT NULL,
    contract_content TEXT NOT NULL,
    policy_content TEXT NOT NULL,
    comparison_result TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_contract_summaries_filename ON contract_summaries(filename);
CREATE INDEX IF NOT EXISTS idx_contract_summaries_created_at ON contract_summaries(created_at);
CREATE INDEX IF NOT EXISTS idx_policy_comparisons_created_at ON policy_comparisons(created_at);
CREATE INDEX IF NOT EXISTS idx_policy_comparisons_filenames ON policy_comparisons(contract_filename, policy_filename);

-- Add updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_contract_summaries_updated_at 
    BEFORE UPDATE ON contract_summaries 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_policy_comparisons_updated_at 
    BEFORE UPDATE ON policy_comparisons 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
