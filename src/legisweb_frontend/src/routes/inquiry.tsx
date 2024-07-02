import { Badge, Col, Image, ListGroup, Row } from "react-bootstrap";
import { useSelector } from "react-redux";
import { useLoaderData } from "react-router-dom";
import { RootState } from "../app/store";
import { contentGenerateId } from "../common";
import Avatar from "../components/avatar";
import SpeakSnippetControl from "../components/snippet-control";
import * as Schema from "../schema";

function SpeakSnippet({
  content,
  contentType,
  person,
  rowIdx,
  idx,
}: {
  content: Schema.ContentElement;
  contentType: string;
  person: Schema.Person;
  rowIdx: number;
  idx: number;
}) {
  const contentIdx = contentGenerateId(contentType, content.id, false);
  const displayText = useSelector(
    (state: RootState) => state.contentElement[contentIdx]?.displayText ?? true
  );
  return (
    <ListGroup.Item className="clearfix" id={contentIdx}>
      <SpeakSnippetControl
        content={content}
        contentIdx={contentIdx}
        displayText={displayText}
      />
      <Badge bg="light" text="dark" className="float-end me-3">
        #{contentType}
      </Badge>
      {rowIdx == 0 && idx == 0 && <h5>{person.name}</h5>}
      {displayText ? (
        <p>{content.value || "<TIDAK TERJUMPA>"}</p>
      ) : (
        <Image
          fluid
          src={"data:image/jpeg;base64, ".concat(content.image || "")}
        />
      )}
    </ListGroup.Item>
  );
}

function SpeakLog({
  value,
  person,
  contentType,
}: {
  value: Array<Schema.ContentElementList>;
  person: Schema.Person;
  contentType: string;
}) {
  return (
    <>
      {value.map((item, rowIdx) => (
        <Row key={rowIdx}>
          <Avatar idx={rowIdx} person={person} />
          <Col md={rowIdx == 0 ? undefined : { offset: 2 }}>
            <ListGroup>
              {item.content_list.map((content, idx) => (
                <SpeakSnippet
                  key={idx}
                  person={person}
                  content={content}
                  contentType={contentType}
                  rowIdx={rowIdx}
                  idx={idx}
                />
              ))}
            </ListGroup>
          </Col>
        </Row>
      ))}
    </>
  );
}

export default function Inquiry() {
  // @ts-expect-error fetching API
  const inquiry: Schema.Inquiry = useLoaderData();
  return (
    <>
      <h1>
        Pertanyaan {inquiry.is_oral ? "Mulut" : "Bertulis"} #{inquiry.number}
      </h1>
      <h2>{inquiry.title}</h2>

      {inquiry.inquirer ? (
        <SpeakLog
          person={inquiry.inquirer}
          value={inquiry.inquiries}
          contentType="pertanyaan"
        />
      ) : (
        <></>
      )}
      {inquiry.respondent ? (
        <SpeakLog
          person={inquiry.respondent}
          value={inquiry.responds}
          contentType="jawapan"
        />
      ) : (
        <></>
      )}
    </>
  );
}
