import { Plus, Save, Trash2 } from "lucide-react";
import { FormEvent, useState } from "react";
import { api, QuestionCreate } from "../api/client";
import { useAuth } from "../auth/AuthContext";

function emptyQuestion(orderIndex: number): QuestionCreate {
  return {
    prompt: "",
    order_index: orderIndex,
    points: 1,
    options: [
      { body: "", is_correct: true },
      { body: "", is_correct: false },
      { body: "", is_correct: false },
      { body: "", is_correct: false }
    ]
  };
}

export function AdminExamBuilderPage() {
  const { token } = useAuth();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [durationMinutes, setDurationMinutes] = useState(30);
  const [questions, setQuestions] = useState<QuestionCreate[]>([emptyQuestion(1)]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function updateQuestion(index: number, patch: Partial<QuestionCreate>) {
    setQuestions((current) => current.map((question, i) => (i === index ? { ...question, ...patch } : question)));
  }

  function updateOption(questionIndex: number, optionIndex: number, body: string) {
    setQuestions((current) =>
      current.map((question, i) =>
        i === questionIndex
          ? {
              ...question,
              options: question.options.map((option, j) => (j === optionIndex ? { ...option, body } : option))
            }
          : question
      )
    );
  }

  function markCorrect(questionIndex: number, optionIndex: number) {
    setQuestions((current) =>
      current.map((question, i) =>
        i === questionIndex
          ? {
              ...question,
              options: question.options.map((option, j) => ({ ...option, is_correct: j === optionIndex }))
            }
          : question
      )
    );
  }

  function addQuestion() {
    setQuestions((current) => [...current, emptyQuestion(current.length + 1)]);
  }

  function removeQuestion(index: number) {
    setQuestions((current) =>
      current
        .filter((_, i) => i !== index)
        .map((question, i) => ({ ...question, order_index: i + 1 }))
    );
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!token) {
      return;
    }
    setError("");
    setMessage("");
    setSaving(true);
    try {
      const cleanedQuestions = questions.map((question, index) => ({
        ...question,
        order_index: index + 1,
        options: question.options.map((option) => ({ ...option, body: option.body.trim() }))
      }));
      if (cleanedQuestions.some((question) => !question.prompt.trim() || question.options.some((option) => !option.body))) {
        throw new Error("Every question and option needs text.");
      }
      await api.createExam(token, {
        title: title.trim(),
        description: description.trim(),
        duration_seconds: durationMinutes * 60,
        questions: cleanedQuestions
      });
      setMessage("Exam created and published.");
      setTitle("");
      setDescription("");
      setDurationMinutes(30);
      setQuestions([emptyQuestion(1)]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create exam");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="page-section wide">
      <div className="page-heading">
        <div>
          <h1>Create exam</h1>
          <p>Build a published exam without changing backend files or static question scripts.</p>
        </div>
      </div>
      <form className="builder-form" onSubmit={submit}>
        <section className="panel form-grid">
          <label>
            Title
            <input value={title} onChange={(event) => setTitle(event.target.value)} required />
          </label>
          <label>
            Duration in minutes
            <input
              type="number"
              min={1}
              value={durationMinutes}
              onChange={(event) => setDurationMinutes(Number(event.target.value))}
              required
            />
          </label>
          <label className="full-span">
            Description
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={3} />
          </label>
        </section>

        <div className="question-list">
          {questions.map((question, questionIndex) => (
            <article className="panel question-panel" key={questionIndex}>
              <div className="question-header">
                <h2>Question {questionIndex + 1}</h2>
                {questions.length > 1 && (
                  <button className="icon-button danger" type="button" onClick={() => removeQuestion(questionIndex)}>
                    <Trash2 size={18} />
                  </button>
                )}
              </div>
              <label>
                Prompt
                <textarea
                  value={question.prompt}
                  onChange={(event) => updateQuestion(questionIndex, { prompt: event.target.value })}
                  rows={3}
                  required
                />
              </label>
              <div className="option-stack">
                {question.options.map((option, optionIndex) => (
                  <label className="option-editor" key={optionIndex}>
                    <input
                      type="radio"
                      name={`correct-${questionIndex}`}
                      checked={option.is_correct}
                      onChange={() => markCorrect(questionIndex, optionIndex)}
                    />
                    <input
                      value={option.body}
                      onChange={(event) => updateOption(questionIndex, optionIndex, event.target.value)}
                      placeholder={`Option ${optionIndex + 1}`}
                      required
                    />
                  </label>
                ))}
              </div>
            </article>
          ))}
        </div>

        {error && <p className="error-text">{error}</p>}
        {message && <p className="success-text">{message}</p>}
        <div className="action-row">
          <button className="secondary-button" type="button" onClick={addQuestion}>
            <Plus size={18} /> Add question
          </button>
          <button className="primary-button" type="submit" disabled={saving}>
            <Save size={18} /> {saving ? "Publishing..." : "Publish exam"}
          </button>
        </div>
      </form>
    </section>
  );
}
