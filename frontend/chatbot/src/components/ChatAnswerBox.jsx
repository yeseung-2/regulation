export default function ChatAnswerBox({ answer, griOriginal }) {
  return (
    <div>
      <div dangerouslySetInnerHTML={{ __html: answer }} />
      {griOriginal && (
        <details className="...">
          <summary>📄 GRI 원문 보기</summary>
          <pre>{griOriginal}</pre>
        </details>
      )}
    </div>
  );
}
