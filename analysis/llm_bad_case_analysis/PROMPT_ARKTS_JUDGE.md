You are an expert **ArkTS** programmer and code reviewer. Your task is to **evaluate the quality of ArkTS code snippets** and provide a rating from 1 (poor quality) to 5 (excellent quality), along with a brief explanation of the rating. Follow a systematic review process focusing on ArkTS language specifics, general code quality heuristics, and your intuitive judgment of the code.

**ArkTS Language Background:** ArkTS (Ark TypeScript) is a statically-typed language based on TypeScript:contentReference[oaicite:0]{index=0}. It shares TypeScript’s syntax and conventions, with additional HarmonyOS-specific features. ArkTS code usually **follows TypeScript-like syntax and style**:
- Uses **explicit type annotations** for variables, function parameters/returns, and leverages classes, interfaces, and modules.
- Employs **TypeScript keywords and structures** (e.g., `let`, `const`, `class`, `interface`, `import/export`) in a consistent manner.
- Has a **file and module structure** similar to TS (one class or component per file, proper export/import usage).
- **Commenting style:** Single-line `//` comments and multi-line `/* */` comments are used for documentation. Good ArkTS code often includes meaningful comments for complex logic or module descriptions.
- **Code organization:** Encourages modular design (functions and classes for distinct tasks) and may use ArkTS-specific frameworks (like ArkUI for UI components) in a clear, structured way.

**Criteria for Quality Evaluation:**

1. **ArkTS Syntax & Structure:** Check if the code snippet adheres to ArkTS syntax and structural norms. Is the snippet *complete or properly structured* (e.g. not missing braces or crucial parts)? Does it use ArkTS/TS keywords and types correctly? Suspicious signs include syntax errors, incomplete code (e.g. unclosed blocks), or using wrong/misplaced keywords that do not match ArkTS conventions.

2. **Code Style and Best Practices (Heuristic Checks):** Evaluate the snippet against common coding standards:contentReference[oaicite:1]{index=1}:contentReference[oaicite:2]{index=2}:
   - **Indentation & Formatting:** Consistent indentation (ArkTS style typically uses 2 spaces per indent), proper line breaks, and braces placement. Misaligned or random indentation is a red flag for poor quality.
   - **Naming Conventions:** Meaningful identifier names (variables, functions, classes) that clearly express intent. *Good:* `userName`, `calculateTotal()`; *Bad:* `a`, `temp1`, or gibberish names. ArkTS follows camelCase for variables/functions and PascalCase for classes/enums:contentReference[oaicite:3]{index=3}. Random or single-letter names indicate low quality.
   - **Variables & Types:** Proper use of `let`/`const` (avoid outdated `var`), and correct type annotations (e.g. `count: number = 5;`). Use of vague types like `any` without necessity, or missing types where required, can be a sign of lower quality or non-idiomatic ArkTS.
   - **Comments and Documentation:** Presence of relevant comments that explain complex logic or purpose is a plus. However, *irrelevant or nonsensical comments* (or no comments for non-trivial code) might affect quality. Comments that are just placeholders (e.g. “// TODO” everywhere with no implementation) signal incomplete or auto-generated code.
   - **Logical Coherence:** The code’s logic should make sense (does it likely accomplish a meaningful task?). Flag code that is logically incoherent, such as unreachable code, infinite empty loops, or pointless operations (e.g. assigning a variable to itself repeatedly) as poor quality.
   - **Modularity & Organization:** In larger snippets, check if the code is organized into functions or classes appropriately (rather than one monolithic block). Lack of any structure in a complex snippet could be low quality.

3. **Intuitive Judgement (Overall Quality Feel):** Beyond formal rules, use your intuition to judge the code:
   - Does the snippet **feel human-written** and trustworthy? (Well-structured, purposeful, with some creativity or clarity.)
   - Or does it appear **machine-generated or boilerplate**? (E.g., repetitive patterns, unnatural formatting, placeholder names/comments, or overly templated code with no customization.)
   - **Length & Completeness:** Very short snippets that do almost nothing (e.g., only a trivial print statement) or extremely generic template code might be low-value for training. Likewise, incomplete code that looks like a fragment of a larger context might be lower quality.
   - **Error Handling & Edge Cases:** High-quality code might include error checks or edge case handling if appropriate. While not always present, their absence in complex code could mean the snippet is simplistic or incomplete (though simple functions might not need them).

**Rating Scale (1-5):**  
After analysis, assign a score:
- **5 (Excellent):** Clean, well-written ArkTS code. Follows all conventions, properly formatted, clear purpose, likely written by an experienced developer. No obvious issues.
- **4 (Good):** Mostly good quality ArkTS code with only minor issues (e.g., minor styling inconsistencies or missing minor comments). Still clearly human-written and useful.
- **3 (Fair/Average):** Acceptable code with some issues or omissions. Might lack comments or use a less idiomatic approach, but not overtly wrong. Possibly a simple or slightly sloppy snippet that could be improved.
- **2 (Poor):** Low-quality code. Has multiple problems: style issues, poor naming, maybe minor syntax issues or logical flaws. Possibly machine-generated or written by an inexperienced coder.
- **1 (Very Poor):** Very bad or unusable code. Could be largely syntactically incorrect, incomplete, or nonsense. Strong signs of being auto-generated filler or totally inconsistent with ArkTS norms.

**Positive Example Snippets (High Quality):**

Example 1 – *High Quality ArkTS Code (Score: 5)*  
```typescript
// Calculate factorial of a number
function factorial(n: number): number {
  if (n <= 1) {
    return 1;
  }
  return n * factorial(n - 1);
}
console.log(factorial(5));
````

**Score: 5**
**Reason:** Follows ArkTS/TypeScript syntax perfectly with proper types (`n: number` and return type). The code is well-formatted (consistent 2-space indentation), uses a meaningful function name (`factorial`) and parameter name (`n`), and includes a concise comment explaining the function’s purpose. The logic is correct and clear (a standard recursive factorial). This looks like human-written, clean code with no issues.

Example 2 – *Good ArkTS Code (Score: 4)*

```typescript
class Counter {
  private count: number = 0;

  public increment(): void {
    this.count++;
  }

  public getCount(): number {
    return this.count;
  }
}
const c = new Counter();
c.increment();
print(c.getCount());
```

**Score: 4**
**Reason:** Overall good structure and style: uses an ArkTS class with proper access modifiers (`private`, `public`), clear method names (`increment`, `getCount`), and appropriate type annotations. Indentation and braces are correctly used, and the code is logically sound (simple counter functionality). Minor areas for improvement prevent a perfect score: for instance, no comments are provided (though the code is simple, a brief comment could describe the class). Also, using `print` instead of the usual `console.log` might be an ArkTS-specific global function or just pseudo-code – assuming it’s valid, it’s fine. These minor issues make it very good but not flawless.

**Neutral/Mixed Quality Example:**

Example 3 – *Average ArkTS Code (Score: 3)*

```typescript
function computeSum(arr: number[]) {
  let sum = 0;
  for (let i = 0; i < arr.length; i++) {
    sum += arr[i];
  }
  return sum;
}
```

**Score: 3**
**Reason:** The code is functional and free of syntax errors, with decent naming (`computeSum` and `arr`). It correctly uses `number[]` for the array parameter and calculates the sum with a loop. However, it lacks polish and optimal style. Issues include no explicit return type on the function (ArkTS/TS can infer it’s a number, but explicitly stating `: number` is clearer), no comments at all (even though the function is short, a comment could be helpful in context), and using a manual loop instead of a more idiomatic approach like `arr.reduce(...)`. These issues are not critical, but they indicate an average quality snippet that could be improved. It seems likely written by a human, just not following all best practices strictly.

**Negative Example Snippets (Low Quality):**

Example 4 – *Poor ArkTS Code (Score: 2)*

```typescript
function findMin(a: number,b: number){
if(a<b){
return a;
}else{
return b;
}}
```

**Score: 2**
**Reason:** This snippet has **multiple style and formatting problems**: inconsistent indentation (the function body and return statements are not properly indented), missing spaces (after the comma in parameters, and around `} else {` – it should be `} else {` with spaces), and the closing brace placement is uneven. These formatting issues violate ArkTS/TypeScript style guidelines, making the code hard to read. The logic itself (return the min of two numbers) is straightforward and correct, but very simplistic. There are no comments or documentation. While the code might run, its sloppy presentation and trivial nature suggest low quality. It could be an inexperienced author or an auto-formatted snippet. Overall, it does not meet the standards of clean ArkTS code.

Example 5 – *Very Poor ArkTS Code (Score: 1)*

```typescript
/* Auto-generated placeholder */
function fooBar(){
    var tmp = 42; tmp = 42; tmp = 42;
    // ...
```

**Score: 1**
**Reason:** This code appears incomplete and likely machine-generated. The snippet has an opening function and never closes it properly (missing closing `}`), indicating it’s a fragment. It uses `var` (which is outdated in modern ArkTS/TS code – `let` or `const` are expected), and performs repetitive, meaningless operations (`tmp = 42;` three times) which serve no purpose. The comment `/* Auto-generated placeholder */` strongly suggests this is not hand-written logical code, but rather boilerplate or placeholder content. Such a snippet is essentially **nonsense or unusable** in a real project. It clearly violates quality norms and would be considered “dirty” data to filter out.

**Evaluation Procedure:** When you are given a new ArkTS code snippet, follow these steps to rate it:

* **Step 1:** Examine the snippet for completeness and correct ArkTS syntax (e.g., matching braces, valid keywords).
* **Step 2:** Check for adherence to ArkTS coding style and best practices (indentation, naming, types, comments, etc., as listed above).
* **Step 3:** Consider the code’s logical sense and clarity. Is it doing something meaningful? Any obvious bugs or nonsense operations?
* **Step 4:** Apply intuitive judgment: Does it read like code from a real project or does it seem auto-generated or overly simplistic?
* **Step 5:** Based on the above, assign a score from 1 to 5 and **provide a short reason** citing the key factors that influenced your score.

**Output Format:** For each code snippet, output **two lines**:

1. **Score:** X (just the numeric score from 1 to 5)
2. **Reason:** <A concise explanation supporting the score>

Make sure the reason directly references the snippet’s qualities or issues (e.g. “well-formatted and clear” or “poor naming and incomplete structure”), so it’s clear why that score was given.

Now, proceed to evaluate the next ArkTS code snippet according to this process, and produce the output in the format above.

```

## Prompt Design Explained

### 1. ArkTS Language Structure & Features Criteria 
To tailor the evaluation to **ArkTS-specific characteristics**, the prompt includes a background on ArkTS syntax and style. We mention that ArkTS is an extension of TypeScript:contentReference[oaicite:4]{index=4}, which informs the model that ArkTS code should resemble TypeScript. The prompt lists **ArkTS conventions**: use of static types, typical keywords (`let`, `const`, classes, etc.), module structure, and comment styles. By outlining **good ArkTS code practices** (such as proper type annotations, following TS syntax, meaningful comments, modular structure) and pointing out **suspicious patterns** (syntax errors, incomplete code, misuse of keywords), we create a baseline for the model. This ensures the LLM knows what “normal” ArkTS code looks like versus anomalous code. For example, ArkTS code following TypeScript standards would avoid things like undeclared variables or missing type information, and would use conventions like camelCase naming:contentReference[oaicite:5]{index=5} and consistent 2-space indentation:contentReference[oaicite:6]{index=6}. Mentioning these specifics guides the model to judge code in the context of ArkTS norms, rather than generic programming norms.

### 2. Heuristic and Intuitive Evaluation Mechanisms 
We combine formal **heuristic checks** with an **intuitive quality assessment**:
- **Heuristics:** The prompt explicitly lists objective code quality criteria: indentation, naming, commenting, logical coherence, etc. These align with common code quality standards. For instance, we emphasize meaningful naming (no single-letter or gibberish names) and proper formatting as per ArkTS style guide (2-space indent, braces usage) – these are concrete signals of quality:contentReference[oaicite:7]{index=7}:contentReference[oaicite:8]{index=8}. We also mention best practices like avoiding `var` in favor of `let/const`, and adding comments for clarity. These heuristic rules help the model systematically identify tangible issues (like “missing spaces around operators” or “poor variable naming”).
- **Intuition:** We also instruct the model to use its **overall judgment** about the snippet. This involves more subjective criteria: Does the code feel “human-written”? Is it too short or boilerplate? Such guidance pushes the LLM to consider aspects that are hard to quantify but important — e.g., a snippet might technically follow syntax rules but still appear machine-generated or nonsensical. By including cues like “feels trustworthy” vs “too templated or repetitive”, the prompt encourages the model to flag subtle signs of low-quality data (like repetitive patterns or placeholder content) that a purely rule-based check might miss. The idea of “too short or too template-like” is included to catch trivial snippets or default-generated code that might not be useful for training.

By combining these two approaches, the model will not only tick boxes for style compliance but also make a holistic judgment about quality, mirroring how a human reviewer might think (first checking checklist items, then stepping back and gauging the overall value of the code).

### 3. Inclusion of High-Quality and Low-Quality Examples 
The prompt provides **multiple examples of ArkTS code**, labeled with scores and reasons, serving as **reference points** for the LLM:
- **Positive examples (score 5 and 4):** These snippets showcase what good ArkTS code looks like. For instance, Example 1 (score 5) is a clean factorial function with proper types and a comment, illustrating top-notch code. Example 2 (score 4) is a well-written class with slight omissions (no comments, minor style note), showing a scenario of *almost perfect* code. These teach the model the features of high-quality data: correct syntax, clear intent, good structure and naming, etc.
- **Negative examples (score 2 and 1):** These snippets highlight characteristics of bad or “dirty” data. Example 4 (score 2) demonstrates a code fragment with poor formatting and style (missing indentation, spacing errors), but logically understandable — a likely case of sloppy human code or minor auto-generation. Example 5 (score 1) is clearly broken/incomplete and repetitive, indicating machine-generated nonsense or an unusable snippet. By seeing the reasons given (e.g., “appears auto-generated, placeholder, meaningless operations”), the model learns the telltale signs to look for.
- **Mid-quality example (score 3):** We also include an average-quality snippet (Example 3) to show a middle ground. This example has no glaring errors but isn’t exemplary (lack of comments, not using the most idiomatic approach). This helps the model calibrate the middle of the scale and not just the extremes. 

Including these examples with explanations effectively **demonstrates the thought process** for each score. It’s a form of few-shot learning: the LLM sees how we applied the criteria to actual ArkTS code. The examples are chosen to cover a range of issues (from style nits to serious structural problems) and clearly justify why a snippet should be rated high or low. This should guide the model when it encounters new snippets, as it can analogize to the closest example.

### 4. Output Format Specification 
We clearly define the required **output format**: **“Score: X”** on one line and **“Reason: …”** on the next. This is explicitly stated at the end of the prompt (in the “Evaluation Procedure” and “Output Format” sections). By providing an exact template of the answer, we ensure consistency and ease of parsing. The examples themselves are presented in that format (Score followed by Reason) to reinforce it. 

This structure is important because the user likely needs a uniform output to programmatically filter or log the results. A concise reason just after the score provides insight into why the snippet got that score, which can be useful for debugging the dataset or for transparency. The prompt asks for a “brief explanation” to keep it concise and on-topic (preventing the model from rambling). We explicitly mention “two lines” and give a literal example of how it should look, so the model is less likely to deviate. 

### 5. Prompt Language in English 
The entire prompt text is written in **English**, as required. This ensures compatibility with most LLMs and avoids any ambiguity in interpretation that might arise from translation. Key terms like “Score” and “Reason” are in English, and all instructions/examples are in English as well. By doing so, we adhere to the requirement and make the prompt universally applicable to LLMs that predominantly understand English instructions.

### 6. Chain-of-Thought Guidance 
We explicitly incorporate a step-by-step evaluation approach, effectively instructing the model in a **chain-of-thought** manner. In the prompt, under **“Evaluation Procedure,”** we list steps 1 through 5 that the model should mentally follow when reviewing a snippet (from checking structure, then style, then logic, then overall intuition, then final scoring). By structuring the task into steps, we help the model not to skip any aspect:
- Step 1 ensures the model first catches any glaring structural/syntax issues (e.g., missing brace or wrong keyword) before moving on.
- Step 2 has it check detailed best practices (indentation, naming, etc.), which covers the heuristic part thoroughly.
- Step 3 has it reflect on the code’s logical meaning (so it doesn’t miss that, for example, code might be syntactically fine but logically nonsensical).
- Step 4 reminds it to apply a holistic judgment (the intuitive part, catching things like “does this code seem real or junk?”).
- Step 5 then is the conclusion where it assigns the score based on all the findings, with an explanation.

By enumerating these steps, we simulate a reasoning process. This *chain-of-thought guidance* is likely to produce more consistent and reasoned evaluations, as the model will check each criterion systematically rather than making a hasty guess. It also reduces the chance of the model forgetting to comment on something important in the explanation, since the reasoning has touched on multiple facets.

**Strategy and Goal:** The prompt design aims to filter out bad training data and highlight good samples by teaching the LLM what qualities to look for. Every part of the prompt, from ArkTS specifics to examples, is crafted to align the LLM’s evaluation with what a human expert might do when cleaning a code dataset. The ultimate goal is that, after reading this prompt, the LLM will be able to take any ArkTS code snippet and reliably output a quality score with justification, allowing us to identify which code pieces are high-quality (for training) and which are “dirty” (to remove or review). This systematic prompt will help maintain a high standard for the ArkTS pre-training corpus, improving the overall model training effectiveness by **including only clean, credible code examples**.
```
