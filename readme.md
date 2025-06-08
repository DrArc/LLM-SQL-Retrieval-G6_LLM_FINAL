# LLM-SQL-Retrieval

This repo is used for a workshop on using LLMs for SQL Retrieval. Its a very direct pipeline that is augmented with database schema injection and a self-debugging mechanism for failed queries. You can find more, super interesting approaches by going through the papers in this leaderboard : https://bird-bench.github.io/

## Project Structure

The project follows a modular directory structure, which allows for easy extension and customization.

The original structure can be found and documented on my other [repo](https://github.com/jomiguelcarv/aia25-studio-agent).

## Getting Started

### Configuration

1. **API Keys**

   - Navigate to the `server/` directory and create a `keys.py` file.
   - Add your API keys or authentication credentials here. This file is not uploaded to GitHub for security reasons.
2. **Local or Cloud LLM Configuration**

   - In the `server/config.py` file, you will find the logic to switch between using a local LLM or a cloud-based LLM.
   - Customize this file to select the appropriate LLM for your project. You can add any new local models in this configuration file.

### Working with the Code

- **Adding New LLM Calls**If you need to add new LLM calls, modify the `llm_calls.py` file. This file is where you define different system prompts and interface with the LLM API.
- **Creating New Knowledge Databases**To add new knowledge databases (such as post-processed embeddings), place the new JSON files in the `knowledge/` directory. Modify `embeddings.json` or add new files To learn how to create the embeddings, visit my other repository [Knowledge-Pool-RAG](https://github.com/jomiguelcarv/LLM-Knowledge-Pool-RAG).
- **Main Pipeline**The `main.py` file orchestrates the pipeline for calling LLM functions and integrating the responses into your design workflow. You can expand this file as needed to suit your design assistant copilot’s business logic.
- **Utility Functions**
  The `utils/rag_utils.py` file contains functions related to Retrieval-Augmented Generation (RAG), useful for incorporating external knowledge into your LLM queries. You can add additional utility functions to extend the project’s capabilities.
