import { Injectable, inject } from '@angular/core';
import { Firestore, collection, collectionData } from '@angular/fire/firestore';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class InvestigationsService {
  firestore: Firestore = inject(Firestore)
  investigations$: Observable<any[]>;

  constructor() { }

  getInvestigations() {
    this.investigations$ = collectionData(collection(this.firestore, 'investigations'))
    return this.investigations$
  }
}
