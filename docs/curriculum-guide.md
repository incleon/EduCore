# Curriculum guide

Imagine you are playing a huge, exciting video game called **"College."** To win the game and get your diploma, you have to follow a specific path, complete levels, and collect points. 

In our system, we organize this game using three main things: **Curricula**, **Curriculum Versions**, and **Curriculum Subjects**. 

Let's break them down! 🚀

---

## 1. 📘 The Curriculum (The Big Game Title)

Think of a **Curriculum** as the *Name of the Video Game* or the *Title of a Big Recipe Book*. It just tells you what the whole adventure is about.

- **What it is:** It is the big picture. It says, "This is the plan for students who want to become Computer Engineers."
- **Example:** "B.Tech in Computer Science" or "Master of Business (MBA)".

At this point, we just know the name of the adventure, but we don't know the rules or the levels yet!

---

## 2. 🔄 Curriculum Versions (The Game Updates / Editions)

Have you ever played a game that gets an update? Maybe in the 2020 version of the game, you had to fight a dragon, but in the 2024 version, they added robots instead! 

That’s exactly what a **Curriculum Version** is! 

Schools change what they teach as the world changes. So, instead of throwing away the whole game, they just make a new **Version**. 

- **What it is:** A specific set of rules for a specific group of students (called a batch). 
- **Example:** 
  - **Version 1 (2020 Edition):** Students learn how to build simple websites. 
  - **Version 2 (2024 Edition):** The world now has ChatGPT, so the school creates a new version where students learn about Artificial Intelligence! 

*Why do we need this?* Because a student who started school in 2020 needs to finish the rules they started with (Version 1), while a new student starting in 2024 will follow the new rules (Version 2). No one gets confused!

---

## 3. 🧩 Curriculum Subjects (The Levels & Quests)

Now we know the game (Curriculum) and we know which update we are playing (Version). But what do we actually *do*? 

Enter **Curriculum Subjects**! These are the actual **Levels**, **Boss Fights**, and **Quests** you have to complete to win.

- **What it is:** The specific classes you must take during a specific time (Semester).
- **Example:** 
  - **Semester 1:** You must defeat the "Basic Math" monster and complete the "Intro to Coding" puzzle. (These are mandatory subjects!)
  - **Semester 2:** You get to choose your own adventure! Do you want to take "Art" or "Music"? (These are called elective subjects!)

Each subject gives you **Credits** (like XP or experience points). You need enough points to pass the level (Semester) and move on to the next one!

---

## 🍔 The Burger Example (Putting it all together!)

Let's pretend we are running a restaurant instead of a school.

1. **Curriculum (The Menu Item):** The "Super Mega Burger." 
2. **Curriculum Version (The Recipe Update):** 
   - *2021 Recipe Version:* Beef patty, cheese, and ketchup.
   - *2024 Recipe Version:* We upgraded it! Now it has a beef patty, cheese, *bacon*, and *special secret sauce*.
3. **Curriculum Subjects (The Ingredients):**
   - For the 2024 Version, Step 1 (Semester 1) is to get the **Bun** and **Beef**. (Mandatory!)
   - Step 2 (Semester 2) is choosing your toppings: Pick either **Pickles** or **Onions**. (Electives!)

---

## 💻 How to Use Them in Our CMS (With Examples!)

Now that we know how it works, let's see how we actually click buttons and type things in our College Management System (CMS) to set this up!

### Step 1: Create the Curriculum
First, you tell the CMS that a new degree or program exists.
- **Where to go:** Admin Dashboard -> Academic Structure -> Curricula
- **What to do:** Click "Add New Curriculum".
- **CMS Example:** 
  - **Course:** B.Tech (Bachelor of Technology)
  - **Branch:** Computer Science Engineering (CSE)
  - **Name:** "B.Tech CSE Core Curriculum"

### Step 2: Create a Curriculum Version
Next, you tell the CMS which "rulebook edition" you are making.
- **Where to go:** Under the Curriculum you just created, click "Manage Versions".
- **What to do:** Click "Add New Version".
- **CMS Example:**
  - **Version Code:** "CSE-2024-V1"
  - **Title:** "B.Tech CSE - AI & Tech Update 2024"
  - **Effective Year:** 2024
  - **Applicable Batch Start:** 2024 (Meaning students joining in 2024 will follow this!)

### Step 3: Add Curriculum Subjects (The Classes!)
Finally, you put the actual classes into the rulebook for each semester.
- **Where to go:** Open your Version ("CSE-2024-V1") -> Manage Semesters -> Add Subjects.
- **What to do:** Assign subjects to a specific semester.
- **CMS Example:**
  - **Semester 1:** You add "Introduction to Programming" (Mandatory, 4 Credits).
  - **Semester 2:** You add "Data Structures" (Mandatory, 4 Credits) and create an **Elective Group** where students can choose between "Basic Electronics" or "Physics" (Elective, 3 Credits).

### 🎓 How it helps Students in the CMS
When a student (let's call him Alex) logs into the CMS:
1. The CMS sees Alex joined in 2024. 
2. It automatically matches him to the **Curriculum Version "CSE-2024-V1"**.
3. When it's time to pick classes or see his timetable, the CMS only shows him the **Curriculum Subjects** from his specific rulebook. Alex can't accidentally pick a class from the old 2020 version!

---

### 🎉 Summary 

- **Curriculum:** What are we learning? *(e.g., Computer Science)*
- **Curriculum Version:** Which year's rulebook are we following? *(e.g., The 2024 Rulebook)*
- **Curriculum Subjects:** What exact classes do I need to sit in today to win? *(e.g., Math, Science, Art)*

And that's how we keep thousands of students on the right track to graduation without getting lost! 🏆
