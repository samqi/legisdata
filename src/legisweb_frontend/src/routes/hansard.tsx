import Badge from "react-bootstrap/Badge";
import Card from "react-bootstrap/Card";
import Col from "react-bootstrap/Col";
import Image from "react-bootstrap/Image";
import Row from "react-bootstrap/Row";
import { useSelector } from "react-redux";
import { useLoaderData } from "react-router-dom";
import type { RootState } from "../app/store";
import { contentGenerateId } from "../common";
import Avatar from "../components/avatar";
import SpeakLineControl from "../components/snippet-control";
import type * as Schema from "../schema";

function checkIsQuestion(
  item: Schema.Question | Schema.Answer
): item is Schema.Question {
  return "inquirer" in item;
}

function Debate({ debate }: { debate: Schema.Debate }) {
  return (
			<>
				{debate.type === "Speech" ? (
					// @ts-expect-error union type
					<Speech speech={debate.value} />
				) : (
					// @ts-expect-error union type
					<QuestionSession session={debate.value} />
				)}
			</>
		);
}

function QASpeakline({ item }: { item: Schema.Question | Schema.Answer }) {
  return (
			<>
				{item.content_list.map((content, idx) => (
					<SpeakLine
						key={idx}
						idx={idx}
						name={
							checkIsQuestion(item) ? item.inquirer.name : item.respondent.name
						}
						content={content}
						contentType={checkIsQuestion(item) ? "pertanyaan" : "jawapan"}
						person={checkIsQuestion(item) ? item.inquirer : item.respondent}
					/>
				))}
			</>
		);
}

function SpeakLine({
  idx,
  name,
  content,
  contentType,
  person,
}: {
  idx: number;
  name: string;
  content: Schema.ContentElement;
  contentType: string;
  person: Schema.Person;
}) {
  const contentIdx = contentGenerateId(contentType, content.id);
  const displayText = useSelector(
    (state: RootState) => state.contentElement[contentIdx]?.displayText ?? true
  );

  return (
    <>
      <Row id={contentGenerateId(contentType, content.id)}>
        <Avatar idx={idx} person={person} />
        <Col md={idx == 0 ? undefined : { offset: 2 }}>
          <Card>
            <Card.Body className="clearfix">
              <SpeakLineControl
                content={content}
                contentIdx={contentIdx}
                displayText={displayText}
              />
              <Badge bg="light" text="dark" className="float-end me-3">
                #{contentType}
              </Badge>
              {idx == 0 ? (
                <Card.Title>{name || "<TIDAK TERJUMPA>"}</Card.Title>
              ) : (
                <></>
              )}
              {displayText ? (
                <p>{content.value || "<TIDAK TERJUMPA>"}</p>
              ) : (
                <Image
                  fluid
                  src={"data:image/jpeg;base64, ".concat(content.image || "")}
                />
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </>
  );
}

function QuestionSession({ session }: { session: Schema.Questions }) {
  return (
    <>
      {session.questions
        .map((question, idx) => (
          <QASpeakline
            key={"question-".concat(idx.toString())}
            item={question}
          />
        ))
        .concat(
          session.answers.map((answer, idx) => (
            <QASpeakline key={"answer-".concat(idx.toString())} item={answer} />
          ))
        )}{" "}
    </>
  );
}

function Speech({ speech }: { speech: Schema.Speech }) {
  return (
    <>
      {speech.content_list.map((content, idx) => (
        <SpeakLine
          key={idx}
          idx={idx}
          name={speech.by.name}
          content={content}
          contentType="ucapan"
          person={speech.by}
        />
      ))}
    </>
  );
}

export default function Hansard() {
  // @ts-expect-error fetching from API
  const hansard: Schema.Hansard = useLoaderData();

  return (
    <>
      <h1>Hansard #{hansard.id}</h1>
      {hansard.debate.map((debate, idx) => (
        <Debate key={idx} debate={debate} />
      ))}
    </>
  );
}
