export interface Person {
  name: string;
  raw: string;
  title: Array<string>;
  area: string | null;
  role: string | null;
  image_url?: string;
}

export interface ContentElement {
  id: number;
  type: string;
  value: string;
  image: string | null;
}

export interface Speech {
  by: Person;
  role: string | null;
  content_list: Array<ContentElement>;
}

export interface Answer {
  respondent: Person;
  role: string | null;
  content_list: Array<ContentElement>;
}

export interface Question {
  inquirer: Person;
  role: string | null;
  content_list: Array<ContentElement>;
  is_oral?: boolean;
}

export interface Questions {
  questions: Array<Question>;
  answers: Array<Answer>;
}

export interface Debate {
  type: string;
  value: Questions | Speech;
}

export interface Hansard {
  id: number;
  present?: Array<Person>;
  absent?: Array<Person>;
  guest?: Array<Person>;
  officer?: Array<Person>;
  debate: Array<Debate>;
}

export interface ContentElementList {
  content_list: Array<ContentElement>;
}

export interface Inquiry {
  id: number;
  is_oral: boolean;
  inquirer: Person | null;
  respondent: Person | null;
  number: number;
  title: string | null;
  inquiries: Array<ContentElementList>;
  responds: Array<ContentElementList>;
  akn: string;
}
