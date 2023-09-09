import { Injectable, inject } from '@angular/core';
import { Firestore, collection, collectionData } from '@angular/fire/firestore';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class CustomerInsightsService {
  firestore: Firestore = inject(Firestore)
  investigations$: Observable<any[]>;

  constructor() { }

  getInvestigations() {
    this.investigations$ = collectionData(collection(this.firestore, 'investigations'), { idField: 'id' })
    return this.investigations$
  }
}
