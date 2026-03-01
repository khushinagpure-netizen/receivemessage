"""
Continuous Chat Handler for Katyayani Organics
Manages conversation history and Gemini AI responses with product context

Features:
- Maintains conversation history per user
- Retrieves relevant products from database
- Generates context-aware responses using Gemini
- Handles multi-turn conversations
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import google.generativeai as genai
from config import GEMINI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Store conversations in memory (can be moved to database)
conversation_history = defaultdict(list)

# System prompt for Katyayani Organics
SYSTEM_PROMPT = """You are a helpful customer service assistant for Katyayani Organics, a premium organic products company.

Your responsibilities:
1. Answer questions about our organic products (they are all natural, chemical-free, and sustainably sourced)
2. Provide product recommendations based on customer needs
3. Share information about product benefits, ingredients, and usage instructions
4. Assist with pricing and availability questions
5. Handle customer inquiries professionally and warmly

Guidelines:
- Be conversational and helpful
- Provide accurate product information when available in context
- Suggest related products when appropriate
- If unsure about specific product details, provide general information about organic products
- Always be honest about product limitations
- Encourage customers to ask more questions

Remember: All Katyayani products are:
✓ 100% Organic
✓ No Harmful Chemicals
✓ Sustainably Sourced
✓ Tested for Quality
✓ Certified Organic"""


class ContinuousChatHandler:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        self.conv_history = defaultdict(list)
        self.products_cache = []
        self.load_products()
    
    def load_products(self):
        """Load products from Supabase"""
        try:
            import supabase
            client = supabase.create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            response = client.table('products').select('*').execute()
            self.products_cache = response.data if hasattr(response, 'data') else []
            logger.info(f"Loaded {len(self.products_cache)} products from database")
        except Exception as e:
            logger.error(f"Error loading products: {str(e)}")
            self.products_cache = []
    
    def search_relevant_products(self, user_message: str, limit: int = 3) -> List[Dict]:
        """Search for relevant products based on user message"""
        if not self.products_cache:
            return []
        
        relevant_products = []
        message_lower = user_message.lower()
        
        for product in self.products_cache:
            # Check if product name or description matches keywords in message
            name = product.get('name', '').lower()
            desc = product.get('description', '').lower()
            category = product.get('category', '').lower()
            benefits = product.get('benefits', '').lower()
            
            # Simple matching - can be improved with NLP
            if any(keyword in name or keyword in desc or keyword in category or keyword in benefits 
                   for keyword in message_lower.split()):
                relevant_products.append(product)
        
        return relevant_products[:limit]
    
    def format_products_context(self, products: List[Dict]) -> str:
        """Format products into context string for Gemini"""
        if not products:
            return ""
        
        context = "\n📦 RELEVANT PRODUCTS:\n"
        for i, product in enumerate(products, 1):
            context += f"\n{i}. **{product.get('name')}**"
            context += f"\n   Price: ₹{product.get('price', 'N/A')}"
            context += f"\n   Category: {product.get('category', 'N/A')}"
            context += f"\n   Description: {product.get('description', 'N/A')}"
            if product.get('benefits'):
                context += f"\n   Benefits: {product.get('benefits')[:150]}..."
            if product.get('rating'):
                context += f"\n   Rating: {product.get('rating')}⭐"
        
        return context
    
    def get_conversation_context(self, user_id: str, limit: int = 5) -> str:
        """Get recent conversation context for continuity"""
        history = self.conv_history.get(user_id, [])
        
        # Get last 'limit' messages
        recent = history[-limit:]
        context = ""
        
        for msg in recent:
            if msg['role'] == 'user':
                context += f"Customer: {msg['content']}\n"
            else:
                context += f"Assistant: {msg['content']}\n"
        
        return context
    
    def build_full_prompt(self, user_message: str, user_id: str) -> Tuple[str, List[Dict]]:
        """Build complete prompt with context and product info"""
        
        # Get conversation context
        conv_context = self.get_conversation_context(user_id)
        
        # Search for relevant products
        relevant_products = self.search_relevant_products(user_message)
        products_context = self.format_products_context(relevant_products)
        
        # Build full prompt
        full_prompt = f"""{SYSTEM_PROMPT}

{products_context}

Previous Conversation:
{conv_context if conv_context else "(No previous messages)"}

Current Customer Message: {user_message}

Provide a helpful, conversational response."""
        
        return full_prompt, relevant_products
    
    def generate_response(self, user_message: str, user_id: str, 
                         max_tokens: int = 500) -> Dict[str, Any]:
        """Generate AI response using Gemini with continuous context"""
        
        try:
            # Build prompt with context
            full_prompt, relevant_products = self.build_full_prompt(user_message, user_id)
            
            # Generate response
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                )
            )
            
            ai_response = response.text
            
            # Store in conversation history
            self.store_message(user_id, 'user', user_message)
            self.store_message(user_id, 'assistant', ai_response)
            
            return {
                'status': 'success',
                'response': ai_response,
                'relevant_products': relevant_products,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'response': "I encountered an error processing your request. Please try again."
            }
    
    def store_message(self, user_id: str, role: str, content: str):
        """Store message in conversation history"""
        self.conv_history[user_id].append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep conversation history to last 50 messages per user
        if len(self.conv_history[user_id]) > 50:
            self.conv_history[user_id] = self.conv_history[user_id][-50:]
    
    def get_conversation_history(self, user_id: str) -> List[Dict]:
        """Get full conversation history for a user"""
        return self.conv_history.get(user_id, [])
    
    def clear_conversation(self, user_id: str):
        """Clear conversation history for a user"""
        if user_id in self.conv_history:
            del self.conv_history[user_id]
            logger.info(f"Conversation cleared for user: {user_id}")
    
    def get_quick_product_info(self, product_name: str) -> Optional[Dict]:
        """Get quick info about a specific product"""
        for product in self.products_cache:
            if product_name.lower() in product.get('name', '').lower():
                return product
        return None
    
    def answer_faq(self, question: str) -> Optional[str]:
        """Answer frequently asked questions"""
        
        faq_responses = {
            'delivery': "We deliver across India with standard delivery in 3-5 business days. Express delivery available for major cities.",
            'return': "We offer 30-day money-back guarantee if you're not satisfied with the product quality.",
            'organic': "All our products are 100% certified organic, free from harmful chemicals and pesticides.",
            'ingredients': "Our products contain only natural ingredients. No artificial colors, flavors, or preservatives.",
            'price': "Our prices reflect the premium quality and sustainability of organic farming. Check our website for current pricing.",
            'payment': "We accept all major credit/debit cards, UPI, and net banking options.",
        }
        
        question_lower = question.lower()
        for key, response in faq_responses.items():
            if key in question_lower:
                return response
        
        return None
    
    def handle_product_inquiry(self, user_message: str, user_id: str) -> Dict[str, Any]:
        """Handle complete product inquiry with continuous chat"""
        
        # Check if it's a FAQ
        faq_answer = self.answer_faq(user_message)
        if faq_answer:
            self.store_message(user_id, 'user', user_message)
            self.store_message(user_id, 'assistant', faq_answer)
            return {
                'status': 'success',
                'response': faq_answer,
                'type': 'faq',
                'timestamp': datetime.now().isoformat()
            }
        
        # Otherwise, generate AI response
        return self.generate_response(user_message, user_id)


# Instantiate handler
chat_handler = ContinuousChatHandler()


def process_user_message(user_id: str, user_message: str) -> Dict[str, Any]:
    """Entry point for processing user messages"""
    logger.info(f"Processing message from {user_id}: {user_message[:50]}...")
    return chat_handler.handle_product_inquiry(user_message, user_id)


def get_user_conversation_history(user_id: str) -> List[Dict]:
    """Get conversation history for a user"""
    return chat_handler.get_conversation_history(user_id)


def reset_user_conversation(user_id: str):
    """Reset conversation for a user"""
    chat_handler.clear_conversation(user_id)


def reload_products():
    """Reload products from database"""
    chat_handler.load_products()
    logger.info("Products reloaded")


if __name__ == "__main__":
    # Test the continuous chat
    user_id = "test_user_123"
    
    test_messages = [
        "Hi, do you have any products for skincare?",
        "What's the price of your best seller?",
        "Can you tell me more about the benefits?",
        "How do I use this product?",
    ]
    
    for message in test_messages:
        print(f"\nUser: {message}")
        response = process_user_message(user_id, message)
        print(f"Assistant: {response.get('response', 'No response')}")
        print("-" * 60)
    
    print("\n📜 FULL CONVERSATION HISTORY:")
    history = get_user_conversation_history(user_id)
    for msg in history:
        print(f"{msg['role'].upper()}: {msg['content'][:100]}...")
