import { Component } from '@angular/core';

@Component({
  selector: 'app-investigations',
  templateUrl: './investigations.component.html',
  styleUrls: ['./investigations.component.scss']
})

interface Column {
  field: string;
  header: string;
  customExportHeader?: string;
}

export class InvestigationsComponent {
 investigations: any

 investigationss = [
  {
      "asins": ["B01X234ABC", "B02Y789DEF"],
      "finished_timestamp": "2023-07-05T11:15:00",
      "started_timestamp": "2023-07-05T09:45:00",
      "status": "in_progress"
  },
  {
      "asins": ["B03Z456GHI", "B04W891JKL"],
      "finished_timestamp": "2023-07-06T12:30:00",
      "started_timestamp": "2023-07-06T10:10:00",
      "status": "completed"
  },
  {
      "asins": ["B05M123NOP", "B06N456QRS"],
      "finished_timestamp": "2023-07-07T13:45:00",
      "started_timestamp": "2023-07-07T11:35:00",
      "status": "started_products"
  },
  {
      "asins": ["B07T789TUV", "B08W012WXZ"],
      "finished_timestamp": "2023-07-08T14:00:00",
      "started_timestamp": "2023-07-08T12:50:00",
      "status": "in_review"
  },
  {
      "asins": ["B09R345YAB", "B010567CDE"],
      "finished_timestamp": "2023-07-09T15:15:00",
      "started_timestamp": "2023-07-09T13:05:00",
      "status": "pending_approval"
  }
]
}
