import json
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk

# Filenames
LESSONS_FILE = 'lessons.json'
PROGRESS_FILE = 'progress.json'

def load_lessons():
    """Load lessons from JSON file."""
    try:
        with open(LESSONS_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data.get('lessons', [])
    except FileNotFoundError:
        # If lessons.json not found, return a placeholder
        return []

def save_progress(progress_record):
    """Save a new progress record to progress.json (locally)."""
    try:
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {"attempts": []}
    
    data["attempts"].append(progress_record)
    
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2)

def calculate_wpm_and_accuracy(typed_text, reference_text, start_time, end_time):
    """Calculate Words Per Minute (WPM) and Accuracy."""
    elapsed_seconds = end_time - start_time
    word_count = len(reference_text.split())
    time_in_minutes = elapsed_seconds / 60.0
    wpm = 0
    if time_in_minutes > 0 and word_count > 0:
        wpm = word_count / time_in_minutes
    
    errors = 0
    for i, char in enumerate(typed_text):
        if i >= len(reference_text):
            # Extra characters beyond the reference
            errors += len(typed_text) - len(reference_text)
            break
        if char != reference_text[i]:
            errors += 1
    # If typed less than reference, the remainder is missed
    if len(typed_text) < len(reference_text):
        errors += (len(reference_text) - len(typed_text))

    total_chars = len(reference_text)
    correct_chars = max(0, total_chars - errors)
    accuracy = (correct_chars / total_chars) * 100 if total_chars else 0

    return round(wpm, 2), round(accuracy, 2)


class TypingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Typing Practice App")
        self.root.geometry("700x500")

        self.lessons = load_lessons()
        if not self.lessons:
            # Simple fallback if no lessons are found
            self.lessons = [{
                "id": 1,
                "title": "No Lessons Found",
                "content": "Please check lessons.json"
            }]

        # Keep track of which lesson is currently selected
        self.current_lesson_index = 0  # We'll default to the first lesson

        # State
        self.selected_lesson = None
        self.start_time = None
        self.user_started_typing = False

        # Build the UI
        self.create_widgets()

        # Immediately load the first lesson by default
        self.load_lesson_by_index(self.current_lesson_index)

    def create_widgets(self):
        # Frame for lesson selection
        lesson_frame = tk.Frame(self.root, padx=10, pady=10)
        lesson_frame.pack(fill='x')
        
        tk.Label(lesson_frame, text="Select Lesson:", font=("Arial", 12)).pack(side='left')

        # Build list of "id: title" strings for the combo
        self.lesson_var = tk.StringVar()
        lesson_titles = [f"{lesson['id']}: {lesson['title']}" for lesson in self.lessons]
        self.lesson_dropdown = ttk.Combobox(
            lesson_frame, 
            textvariable=self.lesson_var, 
            values=lesson_titles,
            state="readonly",
            width=40
        )
        self.lesson_dropdown.pack(side='left', padx=5)
        self.lesson_dropdown.bind("<<ComboboxSelected>>", self.on_lesson_selected)

        # Frame for username
        user_frame = tk.Frame(self.root, padx=10, pady=5)
        user_frame.pack(fill='x')
        tk.Label(user_frame, text="Your Name:", font=("Arial", 12)).pack(side='left')
        self.username_entry = tk.Entry(user_frame)
        self.username_entry.pack(side='left', padx=5)

        # Frame for lesson text
        text_frame = tk.Frame(self.root, padx=10, pady=10)
        text_frame.pack(fill='both', expand=True)
        
        self.lesson_text_label = tk.Label(text_frame, text="", wraplength=680, justify="left", font=("Arial", 14))
        self.lesson_text_label.pack(fill='x', pady=5)

        # Text box for user typing
        self.typed_text = tk.Text(text_frame, height=10, wrap='word', font=("Arial", 12))
        self.typed_text.pack(fill='both', expand=True)
        
        # Bind events
        self.typed_text.bind("<KeyPress>", self.on_key_press)       # Detect first keystroke to start timer
        self.typed_text.bind("<Return>", self.on_return_pressed)    # Shift+Enter detection
        self.typed_text.bind("<KeyRelease>", self.on_text_changed)  # Live grading after each key release

        # Configure text tags for highlighting
        self.typed_text.tag_config("correct", foreground="black", background="lightgreen")
        self.typed_text.tag_config("incorrect", foreground="white", background="red")

        # Buttons frame
        button_frame = tk.Frame(self.root, padx=10, pady=10)
        button_frame.pack(fill='x')
        
        self.submit_button = tk.Button(button_frame, text="Submit", command=self.on_submit)
        self.submit_button.pack(side='left', padx=5)

    def load_lesson_by_index(self, index):
        """Loads the lesson at `index`, updates UI accordingly."""
        if index < 0 or index >= len(self.lessons):
            return  # Out of range, do nothing or handle differently

        self.current_lesson_index = index
        self.selected_lesson = self.lessons[index]

        # Update the combo box text (so user sees the correct selected lesson)
        lesson_titles = [f"{lesson['id']}: {lesson['title']}" for lesson in self.lessons]
        self.lesson_dropdown.set(lesson_titles[index])

        # Display the lesson text
        self.lesson_text_label.config(text=self.selected_lesson['content'])

        # Clear typed text and reset state
        self.typed_text.delete("1.0", tk.END)
        self.user_started_typing = False
        self.start_time = None
        # Also clear any previous highlights
        self.typed_text.tag_remove("correct", "1.0", "end")
        self.typed_text.tag_remove("incorrect", "1.0", "end")

    def on_lesson_selected(self, event):
        """Handle user picking a lesson from the dropdown."""
        selected_str = self.lesson_var.get()  # e.g. "3: Punctuation Practice"
        lesson_id_str = selected_str.split(":")[0].strip()

        # Find the matching lesson index
        for i, lesson in enumerate(self.lessons):
            if str(lesson['id']) == lesson_id_str:
                self.load_lesson_by_index(i)
                break

    def on_key_press(self, event):
        """Start the timer on the first key press."""
        if not self.user_started_typing:
            self.user_started_typing = True
            self.start_time = time.time()

    def on_return_pressed(self, event):
        """
        Detect if SHIFT is pressed along with Enter.
        If SHIFT+Enter => submit. Otherwise => normal newline.
        """
        SHIFT_HELD = event.state & 0x0001
        if SHIFT_HELD:
            # SHIFT+Enter => call on_submit
            self.on_submit()
            # Return "break" to prevent inserting a newline
            return "break"
        else:
            # Normal Enter => allow a newline
            pass

    def on_text_changed(self, event):
        """
        Provide live grading as user types:
        - Compare each typed char with the reference char at the same position.
        - Correct chars => green background
        - Incorrect chars => red background
        """
        if not self.selected_lesson:
            return  # No lesson to compare

        typed_text = self.typed_text.get("1.0", "end-1c")  # current typed text
        reference = self.selected_lesson['content']

        # First, remove old tags
        self.typed_text.tag_remove("correct", "1.0", "end")
        self.typed_text.tag_remove("incorrect", "1.0", "end")

        # Go through each character in typed_text
        for i in range(len(typed_text)):
            index_start = f"1.0 + {i} chars"
            index_end   = f"1.0 + {i+1} chars"
            if i < len(reference) and typed_text[i] == reference[i]:
                self.typed_text.tag_add("correct", index_start, index_end)
            else:
                self.typed_text.tag_add("incorrect", index_start, index_end)

    def on_submit(self):
        """Calculate results, show them for 5 seconds, then load the next lesson."""
        if not self.selected_lesson:
            return  # No lesson selected
        if not self.user_started_typing:
            return  # The user never typed

        end_time = time.time()
        typed_text = self.typed_text.get("1.0", tk.END).rstrip("\n")

        wpm, accuracy = calculate_wpm_and_accuracy(
            typed_text,
            self.selected_lesson['content'],
            self.start_time,
            end_time
        )

        # Save progress
        username = self.username_entry.get().strip() or "Anonymous"
        progress_record = {
            "user": username,
            "lessonId": self.selected_lesson['id'],
            "lessonTitle": self.selected_lesson['title'],
            "timestamp": datetime.now().isoformat(),
            "wpm": wpm,
            "accuracy": accuracy
        }
        save_progress(progress_record)

        # Show results in a Toplevel window for 5 seconds
        self.show_results(wpm, accuracy, end_time - self.start_time)

    def show_results(self, wpm, accuracy, elapsed):
        """Show a popup with results for 5 seconds, then close and load next lesson."""
        result_window = tk.Toplevel(self.root)
        result_window.title("Results")
        
        result_msg = (
            f"Time Taken: {round(elapsed, 2)} seconds\n"
            f"WPM: {wpm}\n"
            f"Accuracy: {accuracy}%"
        )
        tk.Label(result_window, text=result_msg, font=("Arial", 12), padx=20, pady=20).pack()

        # Automatically close result window after 5 seconds, then next lesson
        self.root.after(5000, lambda: self.close_results_and_next(result_window))

    def close_results_and_next(self, result_window):
        """Close the result window and load the next lesson (if any)."""
        result_window.destroy()
        next_index = self.current_lesson_index + 1
        if next_index < len(self.lessons):
            # Load the next lesson
            self.load_lesson_by_index(next_index)
        else:
            # No more lessons
            finished_window = tk.Toplevel(self.root)
            finished_window.title("All Lessons Complete")
            tk.Label(finished_window, 
                     text="Congratulations! You have completed all lessons.",
                     font=("Arial", 14), padx=20, pady=20).pack()
            # Optionally, you could reset self.current_lesson_index = 0 
            # or close the app, etc.

def main():
    root = tk.Tk()
    app = TypingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
