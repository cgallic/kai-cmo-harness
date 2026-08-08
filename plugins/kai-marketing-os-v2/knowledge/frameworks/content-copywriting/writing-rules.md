# SEO Expert Writing Rules Framework

A comprehensive framework for optimizing content for search engines and LLMs, derived from SEO Expert's algorithmic authorship methodology.

## Overview

These writing rules are based on analysis of training datasets used by search engines and language models, primarily:
- **C4 (Colossal Clean Crawled Corpus)**: Clean Wikipedia data used for transformer model training
- **ELI5 (Explain Like I'm 5)**: Reddit subreddit data incorporated after Google's Perspectives update
- **Forum and Discussion Data**: Incorporated after the Helpful Content Update

The rules evolve based on which datasets search engines prioritize. Currently, 90% of practices remain stable because they derive from C4, the foundational dataset for transformer architecture.

---

## Core Writing Rules

### 1. Avoid Long-Form Questions in Headings

**Problem**: Long-form questions combine a question with a conditional declaration, making it harder for LLMs to parse and answer.

**Bad Example**:
```
What happens if the at-fault driver left the scene of an accident?
```

**Structure Analysis**:
- "What happens" = Question
- "if" = Condition
- "the at-fault driver left the scene of accident" = Declaration

**Better Approach**: Break into simpler, shorter headings with clear triples (subject-predicate-object).

```
What to do after a hit-and-run accident
```

**Key Quote**: "Long form question actually is exactly this... A long-form question is the unification of a question with a conditional declaration. If you have this type of question, it's not that easy for LLMs to answer these type of things."

### 2. Keep Headings Short

Use multiple heading levels rather than one long heading. Short questions allow LLMs to follow context more easily.

**Implementation**:
- H2: Broad topic
- H3: Specific subtopic
- H4: Boolean or definitional questions

**Example**:
```markdown
## Car Accident Recovery
### Physical Recovery Timeline
#### Does recovery time vary by injury type?
```

### 3. Hypernym in Heading, Hyponyms in List

Structure content with the general category (hypernym) as the heading and specific examples (hyponyms) as list items, often in parentheses.

**Example**:
```markdown
## Soft Tissue Injuries

Common soft tissue injury types include:
- Whiplash (cervical strain)
- Contusions (bruising)
- Sprains (ligament damage)
- Strains (muscle/tendon damage)
```

**Key Quote**: "Hypernym in the list points with parentheses style... If I create a classification here easily, this is the hypernym here, and whatever I put inside the parenthesis, it becomes hyponym."

### 4. Create 60%+ Difference Between Similar Pages

When creating location-specific or variant pages, ensure at least 60% uniqueness in the answer sections.

**Techniques for Creating Difference**:
1. Change synonyms for key terms (attorney/lawyer, car/auto/vehicle, accident/collision/incident)
2. Reorder heading sections
3. Use different statistics per location
4. Vary vocabulary using thesaurus tools
5. Change parenthetical examples

**Key Quote**: "Create at least 60% difference in answer. That will be helpful."

### 5. Prioritize Uniqueness in Low-Value Headings

For important, high-search-volume headings, maintain relevance. For lower-priority headings, introduce more variation for uniqueness.

**Implementation**:
- H1, primary H2s: Keep more uniform for relevance
- Lower H3s, H4s: Change more for uniqueness
- FAQ sections: Vary question phrasing significantly

### 6. Protect the Triple Structure

Maintain consistent subject-predicate-object relationships within content sections.

**Example Analysis**:
- "What happens" = Subject: Event, Predicate: Happens
- "What to do" = Subject: Person (you), Predicate: Do

Choose one triple structure and maintain it throughout a section.

### 7. Incorporate Forum Language Patterns

After the Perspectives update and Helpful Content Update, Google values forum-style authenticity.

**Characteristics**:
- Personal experience indicators
- First-person language
- Colloquial phrasing
- Community-style Q&A format

**Integration Method**: Include perspectives sections or user-generated content elements with forum-style language while maintaining professionalism.

### 8. Use Methodology-Matched Content Length

If you shorten headings, shorten methodology. If you lengthen headings, lengthen explanations.

**Key Quote**: "If you shorten it, methodology should be also shorter too. If you lengthen it, it should be also basically longer too. They should be following each other."

### 9. Match LLM Training Data Patterns

Different LLMs prefer different writing styles based on their training data.

**Observation**: "If different language models prefer different type of sites for purchases or for visiting, for getting the information. It is basically because the data that you get... If the word seconds or sentence or paragraph seconds for Amazon is closer to the training data of GPT 4.1, it will be choosing this one actually more."

**Implication**: Test content against multiple LLMs to understand which style triggers selection.

### 10. Include Statistics and Numbers

Statistics increase citability and information gain.

**Best Practice**: Add specific numbers, percentages, and data points that provide unique value.

---

## Heading Variation Techniques

### Synonym Replacement Strategy

| Original | Variation 1 | Variation 2 |
|----------|-------------|-------------|
| Car accident attorney | Auto accident lawyer | Vehicle collision counsel |
| Near me | In [city] | Local |
| Best | Top | Leading |
| Houston | H-Town | Greater Houston Area |

### Parenthetical Variations

Add parenthetical phrases to headings for variation:

```markdown
## Car Accident Injuries (Types and Treatments)
## Vehicle Collision Injuries (Common Categories)
## Auto Accident Harm (Classification Guide)
```

### Order Variation

Change the order of list items and subsections between similar pages:

**Page 1**: Demographics, Accident Type, Time of Day
**Page 2**: Time of Day, Demographics, Accident Type

---

## Content Structure Rules

### Modular Content Architecture

If a topic becomes a new page, all details go there. If not, details return to the parent page.

**Key Quote**: "Everything here is modular. If something becomes a new page, all details are going there. If not, details are coming back to this page."

**Implementation**:
```
Parent Page
├── [If search demand exists] → New Page with full details
└── [If no search demand] → Subsection with summary + link to related
```

### Boolean Questions for Detail Sections

Add boolean (yes/no) questions as H4s to expand methodology without creating new pages:

```markdown
### Soft Tissue Injury Recovery

#### Is recovery time affected by injury severity?
[Detailed answer]

#### Do treatment options vary by patient age?
[Detailed answer]
```

---

## Legal/Professional Language Integration

For legal or professional content, maintain legal terminology:

**Bad**: "the other driver"
**Good**: "at-fault driver," "victim," "injured party," "plaintiff"

**Key Quote**: "If you're able to legalize your questions and also answers always, that also would be awesome. Rather than saying just person, saying actually something specific there would be great too."

---

## Tools Mentioned

- **Thesaurus Extensions**: For finding synonyms during variation creation
- **AI Studio (Google)**: For comparing unique vocabulary between documents
- **Python Set Operations**: For identifying unique vs. duplicate words between content pieces
- **GPT Attribute Extractor**: Custom agent for extracting entity attributes

---

## Quick Reference

| Rule | Action |
|------|--------|
| Long-form questions | Break into simple question + separate conditional |
| Heading length | Keep short, use more levels |
| Hypernym/hyponym | General term in heading, specifics in list |
| Page uniqueness | 60%+ difference in answer sections |
| Important headings | Keep uniform for relevance |
| Low-priority headings | Vary for uniqueness |
| Triple structure | Maintain consistent S-P-O |
| Forum language | Include authentic, personal elements |
| Content length | Match heading length to methodology depth |
| Legal terms | Use precise professional vocabulary |

---

## Key SEO Expert Quotes

> "My algorithmic authorship rules actually started from the basic rules of Wikipedia, but not on purpose, because I have seen that Stephen Baker was using this data set for formulating entire information extraction rules."

> "Forum language rules also became important, which actually changed my system one more time."

> "Still, I don't use long form questions or long-form answers in my writing rules. If you look at my headings, usually headings are very short."

> "The good thing is that 90% of these practices are not changing at all because the main reason for that is the C4 actually used for creation of transformers."

---

## Version History

- **2024-2025**: Forum language integration (post-Perspectives/HCU updates)
- **2023**: ELI5 subreddit patterns incorporated
- **Original**: C4/Wikipedia-based rules for featured snippets
