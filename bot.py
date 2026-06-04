import os
import logging
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from database import Database
from config import Config

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize database
db = Database()

# Bot commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when /start is issued."""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    # Register user
    db.register_user(user_id, username)
    
    await update.message.reply_text(
        f"Hello {username}! 👋\n\n"
        f"I'm your task management bot. I can help you track tasks and send reminders.\n\n"
        f"Commands:\n"
        f"/addtask <task> - Add a new task\n"
        f"/mytasks - List all your tasks\n"
        f"/completetask <task_id> - Mark a task as complete\n"
        f"/deletetask <task_id> - Delete a task\n"
        f"/reminders - Show upcoming reminders\n"
    )

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a new task."""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("Please provide a task description. Example: /addtask Buy groceries")
        return
    
    task_description = ' '.join(context.args)
    task_id = db.add_task(user_id, task_description)
    
    await update.message.reply_text(f"✅ Task added successfully! (ID: {task_id})")

async def my_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all pending tasks."""
    user_id = update.effective_user.id
    tasks = db.get_pending_tasks(user_id)
    
    if not tasks:
        await update.message.reply_text("📭 You have no pending tasks!")
        return
    
    message = "📋 Your pending tasks:\n\n"
    for task in tasks:
        message += f"ID: {task['id']} - {task['description']}\n"
        if task['created_at']:
            message += f"   Created: {task['created_at']}\n"
    
    await update.message.reply_text(message)

async def complete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mark a task as complete."""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("Please provide the task ID. Example: /completetask 1")
        return
    
    try:
        task_id = int(context.args[0])
        if db.complete_task(task_id, user_id):
            await update.message.reply_text(f"✅ Task {task_id} marked as complete!")
        else:
            await update.message.reply_text(f"❌ Task {task_id} not found or doesn't belong to you.")
    except ValueError:
        await update.message.reply_text("Please provide a valid task ID number.")

async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a task."""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("Please provide the task ID. Example: /deletetask 1")
        return
    
    try:
        task_id = int(context.args[0])
        if db.delete_task(task_id, user_id):
            await update.message.reply_text(f"🗑️ Task {task_id} deleted successfully!")
        else:
            await update.message.reply_text(f"❌ Task {task_id} not found or doesn't belong to you.")
    except ValueError:
        await update.message.reply_text("Please provide a valid task ID number.")

async def reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show upcoming reminders."""
    user_id = update.effective_user.id
    pending_tasks = db.get_pending_tasks(user_id)
    
    if not pending_tasks:
        await update.message.reply_text("No pending reminders. Add some tasks first!")
        return
    
    message = "⏰ Your reminders:\n\n"
    for i, task in enumerate(pending_tasks[:5], 1):
        message += f"{i}. {task['description']}\n"
    
    await update.message.reply_text(message)

async def broadcast_to_users(context: ContextTypes.DEFAULT_TYPE):
    """Background task: Send periodic reminders to all users."""
    bot = context.bot
    users = db.get_all_users()
    
    for user in users:
        user_id = user['user_id']
        pending_tasks = db.get_pending_tasks(user_id)
        
        if pending_tasks:
            message = f"⏰ Reminder: You have {len(pending_tasks)} pending task(s):\n"
            for task in pending_tasks[:3]:  # Show first 3 tasks
                message += f"• {task['description']}\n"
            
            if len(pending_tasks) > 3:
                message += f"...and {len(pending_tasks) - 3} more"
            
            try:
                await bot.send_message(chat_id=user_id, text=message)
                logger.info(f"Sent reminder to user {user_id}")
            except Exception as e:
                logger.error(f"Failed to send reminder to {user_id}: {e}")

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(Config.TELEGRAM_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addtask", add_task))
    application.add_handler(CommandHandler("mytasks", my_tasks))
    application.add_handler(CommandHandler("completetask", complete_task))
    application.add_handler(CommandHandler("deletetask", delete_task))
    application.add_handler(CommandHandler("reminders", reminders))
    
    # Add background job (runs every 6 hours)
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(broadcast_to_users, interval=21600, first=10)  # 6 hours
    
    # Start the Bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
